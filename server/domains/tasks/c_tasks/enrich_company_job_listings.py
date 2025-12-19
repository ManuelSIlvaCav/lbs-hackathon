"""
Task for enriching job listings for a single company
"""

import time
from bson import ObjectId
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from datetime import datetime
import asyncio
import logging

from domains.companies.repository import company_repository
from domains.job_listings.repository import job_listing_repository
from utils.open_ai_singleton import OpenAISingleton

logger = logging.getLogger("app")

# Configuration
BATCH_SIZE = 15  # Process 15 job listings at a time


@shared_task(
    name="domains.tasks.c_tasks.enrich_company_job_listings",
    bind=True,
    soft_time_limit=3600,
    time_limit=4500,
)
def enrich_company_job_listings(
    self,
    company_id: str,
    source_status: str = "scrapped",
    parent_instance_id: str = None,
):
    """
    Enrich job listings for a single company.

    This task:
    1. Gets the company from the database
    2. Gets job listings with specified source_status
    3. Enriches job listings in batches to respect rate limits
    4. Uses async processing to avoid overwhelming the API

    Args:
        company_id: The ID of the company to enrich job listings for
        source_status: Filter for job listings (default: "scrapped" for initial enrichment,
                      use "enriched" for re-validation/revision)
        parent_instance_id: Optional parent task ID for chain tracking

    Returns:
        dict: Summary of the enrichment operation including success/failure counts
    """
    logger.info(
        "Starting enrich_company_job_listings task",
        extra={
            "context": "enrich_company_job_listings",
            "company_id": company_id,
            "batch_size": BATCH_SIZE,
        },
    )

    try:
        # Get company from database
        company = company_repository.get_company_by_id(company_id)
        if not company:
            logger.warning(
                "Company not found in database",
                extra={
                    "context": "enrich_company_job_listings",
                    "company_id": company_id,
                },
            )
            return {
                "status": "failed",
                "company_id": company_id,
                "error": "Company not found",
                "failed_at": datetime.now().isoformat(),
            }

        # Get job listings with specified source_status
        # Build query based on source_status parameter
        if source_status == "scrapped":
            # For initial enrichment: get jobs with null or 'scrapped' status
            status_query = {
                "$or": [{"source_status": None}, {"source_status": "scrapped"}]
            }
        else:
            # For re-validation/revision: get jobs with specific status (e.g., 'enriched')
            status_query = {"source_status": source_status}

        job_listings = job_listing_repository.collection.find(
            {
                "company_id": ObjectId(company_id),
                **status_query,
            }
        ).sort("updated_at", -1)

        job_listing_ids = [str(job["_id"]) for job in job_listings]

        if not job_listing_ids:
            logger.info(
                "No job listings to enrich for company",
                extra={
                    "context": "enrich_company_job_listings",
                    "company_id": company_id,
                    "company_name": company.name,
                },
            )
            return {
                "status": "completed",
                "company_id": company_id,
                "company_name": company.name,
                "total_job_listings": 0,
                "successful": 0,
                "failed": 0,
                "completed_at": datetime.now().isoformat(),
            }

        logger.info(
            "Found job listings to enrich for company",
            extra={
                "context": "enrich_company_job_listings",
                "company_id": company_id,
                "company_name": company.name,
                "job_count": len(job_listing_ids),
            },
        )

        start = time.perf_counter()
        successful_enrichments = 0
        failed_enrichments = 0
        errors = []

        # Process job listings in batches
        for i in range(0, len(job_listing_ids), BATCH_SIZE):
            batch = job_listing_ids[i : i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(job_listing_ids) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(
                "Processing batch for company",
                extra={
                    "context": "enrich_company_job_listings",
                    "company_id": company_id,
                    "company_name": company.name,
                    "batch_num": batch_num,
                    "total_batches": total_batches,
                    "batch_size": len(batch),
                },
            )

            # Process batch asynchronously
            batch_results = asyncio.run(_enrich_batch(batch, company.name))

            # Aggregate results
            for result in batch_results:
                if result["success"]:
                    successful_enrichments += 1
                else:
                    failed_enrichments += 1
                    errors.append(
                        {
                            "job_listing_id": result["job_listing_id"],
                            "error": result["error"],
                        }
                    )

        request_time = time.perf_counter() - start

        logger.info(
            f"Completed enrichment for company {company.name}",
            extra={
                "context": "enrich_company_job_listings",
                "company_id": company_id,
                "company_name": company.name,
                "processed": len(job_listing_ids),
                "elapsed_time": round(request_time, 2),
            },
        )

        summary = {
            "status": "completed",
            "company_id": company_id,
            "company_name": company.name,
            "total_job_listings": len(job_listing_ids),
            "successful": successful_enrichments,
            "failed": failed_enrichments,
            "errors": errors[:50],  # Limit errors in response
            "total_errors": len(errors),
            "completed_at": datetime.now().isoformat(),
        }

        return summary

    except SoftTimeLimitExceeded as t:
        logger.error(
            "Task time limit exceeded in enrich_company_job_listings",
            extra={
                "context": "enrich_company_job_listings",
                "company_id": company_id,
                "error_msg": str(t),
            },
            exc_info=True,
        )
        return {
            "status": "failed",
            "company_id": company_id,
            "error": "Task time limit exceeded",
            "failed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(
            "Failed to execute enrich_company_job_listings task",
            extra={
                "context": "enrich_company_job_listings",
                "company_id": company_id,
                "error_msg": str(e),
            },
            exc_info=True,
        )
        return {
            "status": "failed",
            "company_id": company_id,
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }


async def _enrich_batch(job_listing_ids: list, company_name: str) -> list:
    """
    Enrich a batch of job listings asynchronously.

    Args:
        job_listing_ids: List of job listing IDs to enrich
        company_name: Name of the company for logging

    Returns:
        List of results with success/failure status
    """

    tasks = []
    for job_id in job_listing_ids:
        tasks.append(_enrich_single_job(job_id, company_name))

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    batch_results = []
    for i, result in enumerate(results):
        job_id = job_listing_ids[i]
        if isinstance(result, Exception):
            batch_results.append(
                {
                    "job_listing_id": job_id,
                    "success": False,
                    "error": str(result),
                }
            )
        else:
            batch_results.append(result)

    # Check rate limits after batch
    rate_info = OpenAISingleton.get_rate_limits()
    if rate_info.remaining_requests is not None:
        logger.info(
            f"Batch complete - OpenAI rate limits: {rate_info.remaining_requests}/{rate_info.limit_requests} requests remaining",
            extra={
                "context": "enrich_batch",
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

    return batch_results


async def _enrich_single_job(job_id: str, company_name: str) -> dict:
    """
    Enrich a single job listing.

    Args:
        job_id: Job listing ID to enrich
        company_name: Name of the company for logging

    Returns:
        Dict with success status and error if failed
    """
    try:
        result = await job_listing_repository.enrich_job_listing(job_id)

        if result:
            return {
                "job_listing_id": job_id,
                "success": True,
                "error": None,
            }
        else:
            return {
                "job_listing_id": job_id,
                "success": False,
                "error": "Enrichment returned None",
            }

    except Exception as e:
        logger.error(
            "Failed to enrich job listing",
            extra={
                "context": "enrich_company_job_listings",
                "job_listing_id": job_id,
                "company_name": company_name,
                "error_msg": str(e),
            },
        )
        return {
            "job_listing_id": job_id,
            "success": False,
            "error": str(e),
        }
