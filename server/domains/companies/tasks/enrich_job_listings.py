"""
Task for enriching job listings for followed companies
"""

import time
from celery import shared_task
from datetime import datetime
import asyncio
import logging

from ..repository import company_repository
from .utils import get_followed_company_ids

from domains.job_listings.repository import job_listing_repository

logger = logging.getLogger("app")

# Configuration

BATCH_SIZE = 12  # Process 12 job listings at a time


@shared_task(name="domains.companies.tasks.enrich_job_listings")
def enrich_job_listings():
    """
    Enrich job listings for all companies that are followed by at least one candidate.

    This task:
    1. Finds all companies that have at least one follower
    2. For each company, gets job listings with source_status null or 'scraped'
    3. Enriches job listings in batches to respect rate limits
    4. Uses async processing with batch size of 10 to avoid overwhelming the API

    Returns:
        dict: Summary of the enrichment operation including success/failure counts
    """
    logger.info(
        "Starting enrich_job_listings task",
        extra={
            "context": "enrich_job_listings",
            "batch_size": BATCH_SIZE,
        },
    )

    try:

        followed_company_ids = get_followed_company_ids()

        if not followed_company_ids:
            logger.info("No followed companies found, skipping enrichment")
            return {
                "status": "completed",
                "total_companies": 0,
                "total_job_listings": 0,
                "successful": 0,
                "failed": 0,
                "errors": [],
            }

        total_job_listings = 0
        successful_enrichments = 0
        failed_enrichments = 0
        errors = []

        # Process each followed company
        for company_id in followed_company_ids:
            try:
                company_id_str = str(company_id)
                logger.info(
                    "Processing job listings for company",
                    extra={
                        "context": "enrich_job_listings",
                        "company_id": company_id_str,
                    },
                )

                # Get company from database
                company = company_repository.get_company_by_id(company_id_str)
                if not company:
                    logger.warning(
                        "Company not found in database",
                        extra={
                            "context": "enrich_job_listings",
                            "company_id": company_id_str,
                        },
                    )
                    continue

                # Get job listings with source_status null or 'scraped'
                job_listings = job_listing_repository.collection.find(
                    {
                        "company_id": company_id,
                        "$or": [{"source_status": None}, {"source_status": "scraped"}],
                    }
                )

                job_listing_ids = [str(job["_id"]) for job in job_listings]

                if not job_listing_ids:
                    logger.info(
                        "No job listings to enrich for company",
                        extra={
                            "context": "enrich_job_listings",
                            "company_id": company_id_str,
                            "company_name": company.name,
                        },
                    )
                    continue

                total_job_listings += len(job_listing_ids)

                logger.info(
                    "Found job listings to enrich for company",
                    extra={
                        "context": "enrich_job_listings",
                        "company_id": company_id_str,
                        "company_name": company.name,
                        "job_count": len(job_listing_ids),
                    },
                )

                start = time.perf_counter()

                # Process job listings in batches
                for i in range(0, len(job_listing_ids), BATCH_SIZE):
                    batch = job_listing_ids[i : i + BATCH_SIZE]
                    batch_num = (i // BATCH_SIZE) + 1
                    total_batches = (
                        len(job_listing_ids) + BATCH_SIZE - 1
                    ) // BATCH_SIZE

                    logger.info(
                        "Processing batch for company",
                        extra={
                            "context": "enrich_job_listings",
                            "company_id": company_id_str,
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
                                    "company_id": company_id_str,
                                    "company_name": company.name,
                                    "job_listing_id": result["job_listing_id"],
                                    "error": result["error"],
                                }
                            )

                request_time = time.perf_counter() - start

                logger.info(
                    f"Completed enrichment for company {company.name}",
                    extra={
                        "context": "enrich_job_listings",
                        "company_id": company_id_str,
                        "company_name": company.name,
                        "processed": len(job_listing_ids),
                        "time_taken_secs": f"{request_time * 1000:.0f} ms",
                    },
                )

            except Exception as e:
                logger.error(
                    f"Failed to process company {company_id_str}",
                    extra={
                        "context": "enrich_job_listings",
                        "company_id": company_id_str,
                        "error_msg": str(e),
                    },
                    exc_info=True,
                )

        summary = {
            "status": "completed",
            "total_companies": len(followed_company_ids),
            "total_job_listings": total_job_listings,
            "successful": successful_enrichments,
            "failed": failed_enrichments,
            "errors": errors[:50],  # Limit errors in response
            "total_errors": len(errors),
            "completed_at": datetime.now().isoformat(),
        }

        logger.info(
            "Completed enrich_job_listings task",
            extra={"context": "enrich_job_listings", **summary},
        )

        return summary

    except Exception as e:
        logger.error(
            "Failed to execute enrich_job_listings task",
            extra={"context": "enrich_job_listings", "error_msg": str(e)},
            exc_info=True,
        )
        return {
            "status": "failed",
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

    return batch_results


async def _enrich_single_job(job_id: str, company_name: str) -> dict:
    """
    Enrich a single job listing.

    Args:
        job_id: Job listing ID to enrich
        company_name: Name of the company for logging
        repository: Job listing repository instance

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
                "context": "enrich_job_listings",
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
