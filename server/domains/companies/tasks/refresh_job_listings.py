"""
Task for refreshing job listings for followed companies
"""

from celery import shared_task
from datetime import datetime
import logging

from ..repository import company_repository
from ..data_processor_repository import data_processor_repository
from ..providers.provider import provider_get_job_listings
from .utils import get_followed_company_ids

logger = logging.getLogger("app")


@shared_task(name="domains.companies.tasks.refresh_companies_job_listings")
def refresh_companies_job_listings():
    """
    Refresh job listings for all companies that are followed by at least one candidate.

    This task:
    1. Finds all companies that have at least one follower
    2. For each company, gets the latest enrichment data
    3. Fetches fresh job listings from the provider
    4. Saves the updated job listings to the database

    Returns:
        dict: Summary of the refresh operation including success/failure counts
    """
    logger.info("Starting refresh_companies_job_listings task")

    try:
        followed_company_ids = get_followed_company_ids()

        if not followed_company_ids:
            logger.info("No followed companies found, skipping refresh")
            return {
                "status": "completed",
                "total_companies": 0,
                "successful": 0,
                "failed": 0,
                "errors": [],
            }

        successful_refreshes = 0
        failed_refreshes = 0
        errors = []

        # Process each followed company
        for company_id in followed_company_ids:
            try:
                company_id_str = str(company_id)
                logger.info(
                    "Processing company",
                    extra={
                        "context": "refresh_companies_job_listings",
                        "company_id": company_id_str,
                    },
                )

                # Get company from database
                company = company_repository.get_company_by_id(company_id_str)
                if not company:
                    logger.warning(
                        "Company not found in database",
                        extra={
                            "context": "refresh_companies_job_listings",
                            "company_id": company_id_str,
                        },
                    )
                    failed_refreshes += 1
                    errors.append(
                        {"company_id": company_id_str, "error": "Company not found"}
                    )
                    continue

                # Get latest enrichment to find provider company ID
                enrichment = data_processor_repository.get_latest_enrichment(
                    company_id_str
                )
                if not enrichment:
                    logger.warning(
                        f"No enrichment data found for company {company_id_str}",
                        extra={
                            "context": "refresh_companies_job_listings",
                            "company_id": company_id_str,
                            "company_name": company.name,
                        },
                    )
                    failed_refreshes += 1
                    errors.append(
                        {
                            "company_id": company_id_str,
                            "company_name": company.name,
                            "error": "No enrichment data found",
                        }
                    )
                    continue

                # Extract provider company ID from enrichment data
                provider_company_id = (
                    enrichment.get("raw_data", {}).get("organization", {}).get("id")
                )

                if not provider_company_id:
                    logger.warning(
                        f"Could not find provider company ID for {company_id_str}",
                        extra={
                            "context": "refresh_companies_job_listings",
                            "company_id": company_id_str,
                            "company_name": company.name,
                        },
                    )
                    failed_refreshes += 1
                    errors.append(
                        {
                            "company_id": company_id_str,
                            "company_name": company.name,
                            "error": "Provider company ID not found in enrichment data",
                        }
                    )
                    continue

                # Fetch fresh job listings from provider
                logger.info(
                    f"Fetching job listings for company {company_id_str}",
                    extra={
                        "context": "refresh_companies_job_listings",
                        "company_id": company_id_str,
                        "company_name": company.name,
                        "provider_company_id": provider_company_id,
                    },
                )

                job_listings = provider_get_job_listings(
                    company_id_str, provider_company_id
                )

                logger.info(
                    f"Successfully refreshed {len(job_listings)} job listings for {company.name}",
                    extra={
                        "context": "refresh_companies_job_listings",
                        "company_id": company_id_str,
                        "company_name": company.name,
                        "job_count": len(job_listings),
                    },
                )

                successful_refreshes += 1

            except Exception as e:
                logger.error(
                    f"Failed to refresh job listings for company {company_id_str}",
                    extra={
                        "context": "refresh_companies_job_listings",
                        "company_id": company_id_str,
                        "error_msg": str(e),
                    },
                    exc_info=True,
                )
                failed_refreshes += 1
                errors.append({"company_id": company_id_str, "error": str(e)})

        summary = {
            "status": "completed",
            "total_companies": len(followed_company_ids),
            "successful": successful_refreshes,
            "failed": failed_refreshes,
            "errors": errors,
            "completed_at": datetime.now().isoformat(),
        }

        logger.info(
            "Completed refresh_companies_job_listings task",
            extra={"context": "refresh_companies_job_listings", **summary},
        )

        return summary

    except Exception as e:
        logger.error(
            "Failed to execute refresh_companies_job_listings task",
            extra={"context": "refresh_companies_job_listings", "error_msg": str(e)},
            exc_info=True,
        )
        return {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }
