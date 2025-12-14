"""
Task to cleanup stale job process locks
"""

import logging
from celery import shared_task

from domains.job_listings.process_repository import job_process_repository

logger = logging.getLogger("app")


@shared_task(name="domains.job_listings.tasks.cleanup_stale_job_processes")
def cleanup_stale_job_processes(hours: int = 2):
    """
    Clean up stale job process locks that have been processing for too long

    This task should be run periodically (e.g., every hour) to clean up locks
    from crashed or hung processes.

    Args:
        hours: Number of hours after which a lock is considered stale (default: 2)

    Returns:
        dict: Summary with count of cleaned locks
    """
    logger.info(
        f"Starting cleanup of stale job process locks (older than {hours} hours)",
        extra={"context": "cleanup_stale_job_processes", "hours": hours},
    )

    cleaned_count = job_process_repository.cleanup_stale_locks(hours=hours)

    summary = {
        "status": "completed",
        "stale_locks_cleaned": cleaned_count,
        "cutoff_hours": hours,
    }

    logger.info(
        "Completed cleanup of stale job process locks",
        extra={"context": "cleanup_stale_job_processes", **summary},
    )

    return summary
