"""
Celery tasks for job listings domain

To use these tasks:
    from domains.job_listings.tasks import test_print_company_jobs

    # Trigger task
    result = test_print_company_jobs.delay(company_id="123")

    # Check status
    print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Optional

logger = get_task_logger(__name__)


@shared_task(bind=True, name="job_listings.test_print_company_jobs")
def test_print_company_jobs(self, company_id: str) -> dict:
    """
    Test task that retrieves all job listings for a company and prints them to console

    Args:
        company_id: Company ID to retrieve jobs for

    Returns:
        dict: Status and count of jobs found
    """
    try:
        from domains.job_listings.repository import job_listing_repository

        logger.info(f"=== Starting job retrieval for company_id: {company_id} ===")

        # Retrieve all job listings for the company
        job_listings = job_listing_repository.get_job_listings_by_company(company_id)

        logger.info(f"Found {len(job_listings)} job listings for company {company_id}")

        # Print each job listing to console
        for idx, job in enumerate(job_listings, 1):
            logger.info(f"\n--- Job #{idx} ---")
            logger.info(f"ID: {job.id}")
            logger.info(f"Title: {job.title}")
            logger.info(f"URL: {job.url}")
            logger.info(f"Location: {job.location}")
            logger.info(f"Origin: {job.origin}")
            logger.info(f"Last Seen: {job.last_seen_at}")
            logger.info(f"Posted At: {job.posted_at}")
            logger.info(f"Source Status: {job.source_status}")
            logger.info(f"Listing Status: {job.listing_status}")

            # Display enriched data if available
            if job.profile_categories:
                logger.info(f"Profile Categories: {', '.join(job.profile_categories)}")

            if job.role_titles:
                logger.info(f"Role Titles: {', '.join(job.role_titles)}")

            if job.employement_type:
                logger.info(f"Employment Type: {job.employement_type}")

            if job.work_arrangement:
                logger.info(f"Work Arrangement: {job.work_arrangement}")

            # Display salary information if available
            if job.salary_range_min or job.salary_range_max:
                salary_info = []
                if job.salary_range_min:
                    salary_info.append(f"Min: {job.salary_range_min}")
                if job.salary_range_max:
                    salary_info.append(f"Max: {job.salary_range_max}")
                if job.salary_currency:
                    salary_info.append(f"Currency: {job.salary_currency}")
                logger.info(f"Salary: {', '.join(salary_info)}")

            logger.info("---")

        logger.info(f"=== Completed job retrieval for company_id: {company_id} ===")

        return {
            "status": "success",
            "company_id": company_id,
            "job_count": len(job_listings),
            "message": f"Successfully printed {len(job_listings)} jobs to console",
        }

    except Exception as e:
        logger.error(f"Failed to retrieve jobs for company {company_id}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60, max_retries=3)
