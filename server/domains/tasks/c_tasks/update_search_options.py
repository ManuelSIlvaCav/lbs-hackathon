"""
Celery task to update search options from job listings
"""

import logging
from celery import shared_task
from datetime import datetime

from domains.job_listings.repository import job_listing_repository
from domains.search_options.repository import search_options_repository

logger = logging.getLogger("app")


@shared_task(name="domains.tasks.c_tasks.update_search_options")
def update_search_options():
    """
    Update search options by aggregating data from enriched job listings

    This task:
    - Extracts all unique countries with their cities
    - Extracts all unique profile categories
    - Extracts all unique role titles
    - Stores them in the search_options collection

    Returns:
        dict: Summary of the update operation
    """
    logger.info("Starting update_search_options task")

    try:
        # Get aggregated data from job listings
        countries = job_listing_repository.get_countries()
        profile_categories = job_listing_repository.get_profile_categories()
        role_titles = job_listing_repository.get_role_titles()

        logger.info(
            f"Aggregated search options data",
            extra={
                "context": "update_search_options",
                "countries_count": len(countries),
                "categories_count": len(profile_categories),
                "roles_count": len(role_titles),
            },
        )

        # Update search options
        result = search_options_repository.update_search_options(
            countries=countries,
            profile_categories=profile_categories,
            role_titles=role_titles,
        )

        summary = {
            "status": "completed",
            "countries_count": len(countries),
            "categories_count": len(profile_categories),
            "roles_count": len(role_titles),
            "completed_at": datetime.now().isoformat(),
        }

        logger.info(
            "update_search_options task completed successfully",
            extra={"context": "update_search_options", **summary},
        )

        return summary

    except Exception as e:
        error_msg = f"Fatal error in update_search_options task: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
        }
