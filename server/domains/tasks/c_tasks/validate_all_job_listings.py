"""
Coordinator task to trigger company-level revision tasks for all companies
"""

import logging
import time
from celery import shared_task, chain

from domains.companies.repository import company_repository
from domains.job_listings.process_repository import (
    job_process_repository,
)
from .enrich_company_job_listings import enrich_company_job_listings

logger = logging.getLogger("app")


@shared_task(name="domains.tasks.c_tasks.validate_all_job_listings", bind=True)
def validate_all_job_listings(self):
    """
    Coordinator task to trigger revision for all followed companies

    This task:
    - Gets all followed companies
    - Triggers a separate task for each company sequentially
    - Uses task-level locking to prevent concurrent coordinator execution
    - Each company task has its own lock

    Returns:
        dict: Summary of triggered tasks
    """
    task_name = "validate_all_job_listings"

    # Try to acquire coordinator lock
    lock = job_process_repository.acquire_lock(task_name, self.request.id)

    if not lock:
        logger.warning(
            "Coordinator task already running, skipping execution",
            extra={"context": "validate_all_job_listings"},
        )
        return {
            "status": "skipped",
            "summary_message": "Another coordinator instance is already running",
        }

    try:
        logger.info(
            "Starting coordinator task to revise all companies",
            extra={
                "context": "validate_all_job_listings",
                "task_id": self.request.id,
            },
        )

        # Clean up stale locks (locks older than 2 hours)
        stale_locks_cleaned = job_process_repository.cleanup_stale_locks(hours=2)
        if stale_locks_cleaned > 0:
            logger.info(
                "Cleaned up stale locks before starting",
                extra={
                    "context": "validate_all_job_listings",
                    "stale_locks_cleaned": stale_locks_cleaned,
                },
            )

        # Get all followed company IDs
        # company_ids = company_repository.get_followed_company_ids()

        companies = company_repository.get_all_companies()
        company_ids = [company.id for company in companies]

        if not company_ids:
            logger.info(
                "No followed companies found",
                extra={"context": "validate_all_job_listings"},
            )
            job_process_repository.release_lock(task_name)
            return {
                "status": "completed",
                "total_companies": 0,
                "tasks_triggered": 0,
            }

        logger.info(
            f"Found {len(company_ids)} companies to process",
            extra={
                "context": "validate_all_job_listings",
                "total_companies": len(company_ids),
            },
        )

        start_time = time.perf_counter()

        # Build chain of company tasks to execute sequentially
        company_tasks = []
        for company_oid in company_ids:
            company_id = str(company_oid)

            # Get company details for logging
            company = company_repository.get_company_by_id(company_id)
            company_name = company.name if company else f"Company {company_id}"

            logger.info(
                f"Adding company to sequential chain: {company_name}",
                extra={
                    "context": "validate_all_job_listings",
                    "company_id": company_id,
                    "company_name": company_name,
                },
            )

            # Add company task signature to chain
            # Pass "enriched" as source_status to re-validate already enriched jobs
            company_tasks.append(
                enrich_company_job_listings.signature(
                    args=(company_id, "enriched", self.request.id),
                    immutable=True,  # Don't pass previous result to next task
                )
            )

        elapsed_time = time.perf_counter() - start_time

        # Execute all company tasks sequentially using chain
        if company_tasks:
            task_chain = chain(*company_tasks)
            result = task_chain.apply_async()

            logger.info(
                f"Started sequential chain of company tasks",
                extra={
                    "context": "validate_all_job_listings",
                    "chain_id": result.id,
                    "total_tasks": len(company_tasks),
                },
            )

        summary = {
            "status": "completed",
            "total_companies": len(company_ids),
            "tasks_triggered": len(company_tasks),
            "chain_id": result.id if company_tasks else None,
            "request_task_id": self.request.id,
            "time_taken_seconds": round(elapsed_time, 2),
            "summary_message": f"Started sequential chain of {len(company_tasks)} company processing tasks",
            "note": "Tasks will execute one after another, not in parallel",
        }

        logger.info(
            "Completed triggering all company tasks",
            extra={
                "context": "validate_all_job_listings",
                **summary,
            },
        )

        # Release lock with completed status
        job_process_repository.release_lock(task_name)
        return summary

    except Exception as e:
        logger.error(
            f"Error in coordinator task",
            extra={
                "context": "validate_all_job_listings",
                "error_msg": str(e),
            },
        )
        # Release lock with failed status
        job_process_repository.release_lock(task_name, str(e))
        raise
