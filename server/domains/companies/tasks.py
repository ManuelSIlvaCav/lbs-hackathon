"""
Celery tasks for company operations

DEPRECATED: This file is kept for backwards compatibility.
Please import tasks from domains.companies.tasks module instead.
"""

# Import tasks from the new modular structure
from .tasks import (
    refresh_companies_job_listings,
    enrich_job_listings,
    get_followed_company_ids,
)

__all__ = [
    "refresh_companies_job_listings",
    "enrich_job_listings",
    "get_followed_company_ids",
]


# Keep the old task definition for backwards compatibility
# but it now delegates to the new module structure
def _old_refresh_companies_job_listings():
    """
    OLD IMPLEMENTATION - Kept for reference only.
    Use refresh_companies_job_listings from tasks module instead.
    """
    pass
