"""
Shared utility functions for tasks
"""

from typing import List
from bson import ObjectId
import logging

logger = logging.getLogger("app")


def get_followed_company_ids() -> List[ObjectId]:
    """
    Get all company IDs that are followed by at least one candidate.

    This is a convenience wrapper around the repository method.

    Returns:
        List[ObjectId]: List of company ObjectIds that have at least one follower
    """
    from domains.companies.repository import company_repository

    logger.info("Fetching companies followed by candidates")

    followed_company_ids = company_repository.get_followed_company_ids()

    logger.info(
        f"Found {len(followed_company_ids)} companies followed by candidates",
        extra={
            "context": "get_followed_company_ids",
            "company_count": len(followed_company_ids),
        },
    )

    return followed_company_ids
