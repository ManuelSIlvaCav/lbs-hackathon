"""
API routes for search options
"""

import logging
from fastapi import APIRouter, HTTPException

from domains.job_listings.models import JobListingOrigin
from domains.job_listings.categories import PROFILE_CATEGORIES

from .repository import search_options_repository

logger = logging.getLogger("app")

router = APIRouter(prefix="/api/search-options", tags=["search-options"])


@router.get("")
async def get_search_options():
    """
    Get current search options including countries, profile categories, and role titles

    These options are aggregated from enriched job listings and updated periodically
    via a background task.

    Note: Cities are work in progress - currently only returns countries.

    Returns:
        dict: Search options with countries, profile_categories, and role_titles
    """
    try:
        options = search_options_repository.get_search_options()

        if not options:
            # Return empty structure if no options exist yet
            return {
                "countries": [],
                "profile_categories": [],
                "role_titles": [],
                "updated_at": None,
            }

        origins = [origin.value for origin in JobListingOrigin]
        role_titles_by_category = {
            category: sorted(roles) for category, roles in PROFILE_CATEGORIES.items()
        }

        return {
            "countries": options.countries,
            "origins": origins,
            "profile_categories": options.profile_categories,
            "role_titles": options.role_titles,
            "role_titles_by_category": role_titles_by_category,
            "updated_at": (
                options.updated_at.isoformat() if options.updated_at else None
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get search options: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get search options: {str(e)}"
        )
