"""
Task to process all enriched job listings for a single company
"""

import asyncio
import logging
import os
import time
from celery import shared_task
from typing import List, Optional
from bson import ObjectId

from domains.job_listings.repository import job_listing_repository
from domains.job_listings.process_repository import (
    job_process_repository,
)
from utils.open_ai_singleton import OpenAISingleton

logger = logging.getLogger("app")

# Configuration
BATCH_SIZE = int(os.getenv("REVISE_BATCH_SIZE", "15"))


@shared_task(
    name="domains.tasks.c_tasks.revise_company_enriched_jobs",
    bind=True,
    max_retries=3,
)
def revise_company_enriched_jobs(
    self, company_id: str, company_name: str, parent_instance_id: Optional[str] = None
):
    """
    Revise all enriched job listings for a single company

    This task:
    - Gets all enriched job listings for the specified company
    - Re-runs enrichment in batches to validate/update the data
    - Deactivates job listings that fail parsing
    - Uses company-level locking to prevent concurrent processing

    Args:
        company_id: String representation of company ObjectId
        company_name: Name of the company (for logging)
        parent_instance_id: Optional parent task ID for chain tracking

    Returns:
        dict: Summary of revision results for this company
    """
    task_name = f"revise_company_{company_id}"

    # Try to acquire company-level lock
    lock = job_process_repository.acquire_lock(
        task_name, self.request.id, parent_instance_id=parent_instance_id
    )

    if not lock:
        logger.warning(
            "Company already being processed, skipping",
            extra={
                "context": "revise_company_enriched_jobs",
                "company_id": company_id,
                "company_name": company_name,
            },
        )
        return {
            "status": "skipped",
            "summary_message": f"Company {company_name} is already being processed",
            "company_id": company_id,
            "company_name": company_name,
        }

    try:
        logger.info(
            "Starting revision of enriched job listings for company",
            extra={
                "context": "revise_company_enriched_jobs",
                "company_id": company_id,
                "company_name": company_name,
                "task_id": self.request.id,
            },
        )

        start_time = time.perf_counter()

        # Get all enriched job listings for this company
        enriched_jobs = list(
            job_listing_repository.collection.find(
                {"company_id": ObjectId(company_id), "source_status": "enriched"}
            ).sort("updated_at", -1)
        )

        if not enriched_jobs:
            logger.info(
                "No enriched jobs found for company",
                extra={
                    "context": "revise_company_enriched_jobs",
                    "company_id": company_id,
                    "company_name": company_name,
                },
            )
            job_process_repository.release_lock(task_name)
            return {
                "status": "completed",
                "company_id": company_id,
                "company_name": company_name,
                "total_jobs": 0,
                "jobs_updated": 0,
                "jobs_deactivated": 0,
                "jobs_failed": 0,
            }

        job_ids = [str(job["_id"]) for job in enriched_jobs]
        total_jobs = len(job_ids)

        logger.info(
            "Found enriched jobs for revision",
            extra={
                "context": "revise_company_enriched_jobs",
                "company_id": company_id,
                "company_name": company_name,
                "job_count": total_jobs,
            },
        )

        total_jobs_updated = 0
        total_jobs_deactivated = 0
        total_jobs_failed = 0

        # Process in batches
        num_batches = (len(job_ids) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(job_ids), BATCH_SIZE):
            batch = job_ids[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            logger.info(
                f"Processing batch {batch_num}/{num_batches} for {company_name}",
                extra={
                    "context": "revise_company_enriched_jobs",
                    "company_id": company_id,
                    "company_name": company_name,
                    "batch_number": batch_num,
                    "total_batches": num_batches,
                    "batch_size": len(batch),
                },
            )

            # Process batch concurrently
            batch_results = asyncio.run(_revise_batch(batch, company_name))

            # Count results
            for result in batch_results:
                if result["status"] == "updated":
                    total_jobs_updated += 1
                elif result["status"] == "deactivated":
                    total_jobs_deactivated += 1
                elif result["status"] == "failed":
                    total_jobs_failed += 1

        elapsed_time = time.perf_counter() - start_time

        summary = {
            "status": "completed",
            "company_id": company_id,
            "company_name": company_name,
            "total_jobs": total_jobs,
            "jobs_updated": total_jobs_updated,
            "jobs_deactivated": total_jobs_deactivated,
            "jobs_failed": total_jobs_failed,
            "time_taken_seconds": round(elapsed_time, 2),
        }

        logger.info(
            "Completed revision of enriched job listings for company",
            extra={
                "context": "revise_company_enriched_jobs",
                **summary,
            },
        )

        # Release lock with completed status
        job_process_repository.release_lock(task_name)
        return summary

    except Exception as e:
        logger.error(
            f"Error processing company: {str(e)}",
            extra={
                "context": "revise_company_enriched_jobs",
                "company_id": company_id,
                "company_name": company_name,
                "error": str(e),
            },
        )
        # Release lock with failed status
        job_process_repository.release_lock(task_name, str(e))
        raise


async def _revise_batch(job_ids: List[str], company_name: str) -> List[dict]:
    """
    Process a batch of job listings concurrently

    Args:
        job_ids: List of job listing IDs to revise
        company_name: Name of the company (for logging)

    Returns:
        List of result dictionaries with job_id and status
    """
    tasks = [_revise_single_job(job_id, company_name) for job_id in job_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    rate_info = OpenAISingleton.get_rate_limits()
    if rate_info.remaining_requests is not None:
        logger.info(
            f"Batch complete - OpenAI rate limits: {rate_info.remaining_requests}/{rate_info.limit_requests} requests remaining",
            extra={
                "context": "revise_batch",
                "company_name": company_name,
                "remaining_requests": rate_info.remaining_requests,
                "limit_requests": rate_info.limit_requests,
                "remaining_tokens": rate_info.remaining_tokens,
                "limit_tokens": rate_info.limit_tokens,
                "reset_token_time": rate_info.reset_token_time,
            },
        )

    reset_time_seconds = OpenAISingleton.get_reset_time_seconds()
    if reset_time_seconds > 0:
        logger.info(
            f"Waiting {reset_time_seconds}s before next batch to respect rate limits"
        )
        await asyncio.sleep(reset_time_seconds)

    return results


async def _revise_single_job(job_id: str, company_name: str) -> dict:
    """
    Revise a single job listing by re-running enrichment

    Args:
        job_id: Job listing ID
        company_name: Name of the company (for logging)

    Returns:
        Dictionary with job_id and status
    """
    try:
        # Re-run enrichment
        result = await job_listing_repository.enrich_job_listing(job_id)

        if result is None:
            logger.error(
                "Failed to revise job listing",
                extra={
                    "context": "revise_single_job",
                    "job_id": job_id,
                    "company_name": company_name,
                },
            )
            return {"job_id": job_id, "status": "failed"}

        # Check if job was deactivated
        if result.source_status == "deactivated":
            return {"job_id": job_id, "status": "deactivated"}

        return {"job_id": job_id, "status": "updated"}

    except Exception as e:
        logger.error(
            f"Error revising job listing: {str(e)}",
            extra={
                "context": "revise_single_job",
                "job_id": job_id,
                "company_name": company_name,
                "error": str(e),
            },
        )
        return {"job_id": job_id, "status": "failed", "error": str(e)}
