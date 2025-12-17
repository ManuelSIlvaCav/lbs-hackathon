"""
Task for enriching job listings for followed companies
"""

from celery import shared_task
from datetime import datetime
import logging

from .utils import get_followed_company_ids
from .enrich_company_job_listings import enrich_company_job_listings

logger = logging.getLogger("app")


@shared_task(name="domains.tasks.c_tasks.enrich_job_listings")
def enrich_job_listings():
    """
    Enrich job listings for all companies that are followed by at least one candidate.

    This task:
    1. Finds all companies that have at least one follower
    2. For each company, calls enrich_company_job_listings task
    3. Aggregates results from all companies

    Returns:
        dict: Summary of the enrichment operation including success/failure counts
    """
    logger.info(
        "Starting enrich_job_listings task",
        extra={
            "context": "enrich_job_listings",
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

        # Process each followed company using the single company task
        for company_id in followed_company_ids:
            try:
                company_id_str = str(company_id)
                logger.info(
                    "Processing company",
                    extra={
                        "context": "enrich_job_listings",
                        "company_id": company_id_str,
                    },
                )

                # Call the single company enrichment task
                result = enrich_company_job_listings(company_id_str)

                # Aggregate results
                if result["status"] == "completed":
                    total_job_listings += result.get("total_job_listings", 0)
                    successful_enrichments += result.get("successful", 0)
                    failed_enrichments += result.get("failed", 0)

                    # Add company context to errors
                    for error in result.get("errors", []):
                        errors.append(
                            {
                                "company_id": company_id_str,
                                "company_name": result.get("company_name", "Unknown"),
                                **error,
                            }
                        )
                else:
                    # Task failed for this company
                    failed_enrichments += 1
                    errors.append(
                        {
                            "company_id": company_id_str,
                            "error": result.get("error", "Unknown error"),
                        }
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
                errors.append(
                    {
                        "company_id": company_id_str,
                        "error": str(e),
                    }
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
