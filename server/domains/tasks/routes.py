"""
API routes for task management and triggering
"""

import logging
from fastapi import APIRouter, HTTPException, Query, status

from .c_tasks import (
    refresh_companies_job_listings,
    enrich_all_job_listings,
    enrich_company_job_listings,
    validate_all_job_listings,
    create_recommendations,
    update_search_options,
)
from domains.job_listings.process_repository import job_process_repository

logger = logging.getLogger("app")

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/refresh-followed-job-listings", response_model=dict)
async def trigger_refresh_followed_companies():
    """
    Manually trigger refresh of job listings for all followed companies

    This endpoint triggers the background task that:
    1. Finds all companies followed by at least one candidate
    2. Fetches fresh job listings from the provider for each company
    3. Updates the database with new job listings

    The task runs asynchronously. Use the returned task_id to check status.

    Returns:
        dict: Task information including task_id and status
    """
    try:
        logger.info("Manually triggering refresh_companies_job_listings task")

        # Trigger the Celery task asynchronously
        task = refresh_companies_job_listings.apply_async()

        return {
            "message": "Job listing refresh task started",
            "task_id": task.id,
            "status": "pending",
            "info": "Task is running in the background. Check task status using the task_id.",
        }

    except Exception as e:
        logger.error(f"Failed to trigger refresh task: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger refresh task: {str(e)}"
        )


@router.post("/enrich-followed-job-listings", response_model=dict)
async def trigger_enrich_followed_companies():
    """
    Manually trigger enrichment of job listings for all followed companies

    This endpoint triggers the background task that:
    1. Finds all companies followed by at least one candidate
    2. Gets job listings with source_status null or 'scraped' (limited to 15 for development)
    3. Enriches job listings in batches of 10 using AI parsing
    4. Extracts structured data (requirements, skills, categories, etc.)

    The task uses rate limiting and batch processing to avoid overwhelming the API.
    The task runs asynchronously. Use the returned task_id to check status.

    Returns:
        dict: Task information including task_id and status
    """
    try:
        logger.info("Manually triggering enrich_all_job_listings task")

        # Trigger the Celery task asynchronously
        task = enrich_all_job_listings.apply_async()

        return {
            "message": "Job listing enrichment task started",
            "task_id": task.id,
            "status": "pending",
            "info": "Task is running in the background. Check task status using the task_id.",
            "note": "Processing in batches of 10 to respect rate limits. Limited to 15 listings per company in development.",
        }

    except Exception as e:
        logger.error(f"Failed to trigger enrichment task: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger enrichment task: {str(e)}"
        )


@router.post("/enrich-company/{company_id}", response_model=dict)
async def trigger_enrich_company(company_id: str):
    """
    Manually trigger enrichment of job listings for a specific company

    This endpoint triggers the background task that:
    1. Gets the specified company from the database
    2. Gets job listings with source_status null or 'scraped'
    3. Enriches job listings in batches using AI parsing
    4. Extracts structured data (requirements, skills, categories, etc.)

    The task uses rate limiting and batch processing to avoid overwhelming the API.
    The task runs asynchronously. Use the returned task_id to check status.

    Args:
        company_id: The MongoDB ObjectId of the company to enrich

    Returns:
        dict: Task information including task_id and status
    """
    try:
        logger.info(
            f"Manually triggering enrich_company_job_listings task for company {company_id}"
        )

        # Trigger the Celery task asynchronously with company_id argument
        task = enrich_company_job_listings.apply_async(args=[company_id])

        return {
            "message": f"Job listing enrichment task started for company {company_id}",
            "task_id": task.id,
            "company_id": company_id,
            "status": "pending",
            "info": "Task is running in the background. Check task status using the task_id.",
        }

    except Exception as e:
        logger.error(
            f"Failed to trigger enrichment task for company {company_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger enrichment task: {str(e)}",
        )


@router.post("/create-recommendations", response_model=dict)
async def trigger_create_recommendations():
    """
    Manually trigger creation of job recommendations for all candidates

    This endpoint triggers the background task that:
    1. Gets all candidates with search preferences (profile_categories and/or role_titles)
    2. For each candidate, searches for job listings matching their preferences
    3. Creates recommendations for matching jobs that don't already exist
    4. Uses bulk operations for performance

    The task runs asynchronously. Use the returned task_id to check status.

    Returns:
        dict: Task information including task_id and status
    """
    try:
        logger.info("Manually triggering create_recommendations task")

        # Trigger the Celery task asynchronously
        task = create_recommendations.apply_async()

        return {
            "message": "Create recommendations task started",
            "task_id": task.id,
            "status": "pending",
            "info": "Task is running in the background. Check task status using the task_id.",
        }

    except Exception as e:
        logger.error(f"Failed to trigger create recommendations task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger create recommendations task: {str(e)}",
        )


@router.post("/update-search-options", response_model=dict)
async def trigger_update_search_options():
    """
    Manually trigger update of search options from job listings

    This endpoint triggers the background task that:
    1. Aggregates unique countries with cities from enriched job listings
    2. Aggregates unique profile categories from enriched job listings
    3. Aggregates unique role titles from enriched job listings
    4. Stores the aggregated data in the search_options collection

    The task runs asynchronously. Use the returned task_id to check status.

    Returns:
        dict: Task information including task_id and status
    """
    try:
        logger.info("Manually triggering update_search_options task")

        # Trigger the Celery task asynchronously
        task = update_search_options.apply_async()

        return {
            "message": "Update search options task started",
            "task_id": task.id,
            "status": "pending",
            "info": "Task is running in the background. Check task status using the task_id.",
        }

    except Exception as e:
        logger.error(f"Failed to trigger update search options task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger update search options task: {str(e)}",
        )


@router.post("/revise-enriched", response_model=dict)
async def trigger_revise_enriched_job_listings():
    """
    Trigger coordinator task to revise all enriched job listings

    This endpoint triggers a coordinator Celery task that:
    - Gets all followed companies
    - Triggers a separate task for each company
    - Each company task processes all its enriched job listings in batches
    - Deactivates listings that fail parsing

    This is useful for:
    - Validating existing enriched data
    - Updating listings with improved parsing logic
    - Cleaning up invalid or outdated job listings

    Benefits of modular approach:
    - Better progress tracking (per company)
    - Parallel processing of different companies
    - Individual company retries on failure
    - Rate limit management per company

    Check worker logs with: `docker-compose logs -f worker`

    Returns:
        dict: Task information including task_id for status tracking
    """
    try:
        # Trigger the coordinator Celery task
        task = validate_all_job_listings.delay()

        return {
            "status": "task_started",
            "message": "Coordinator task to revise all companies has been queued",
            "task_id": task.id,
            "note": "This will trigger separate tasks for each company",
            "instructions": "Check worker logs with: docker-compose logs -f worker",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
        )


@router.post("/revise-company/{company_id}", response_model=dict)
async def trigger_revise_company_job_listings(company_id: str):
    """
    Trigger task to revise enriched job listings for a specific company

    This endpoint triggers a Celery task that:
    - Gets all enriched job listings for the specified company
    - Re-runs AI enrichment on each listing in batches
    - Deactivates listings that fail parsing

    Args:
        company_id: ID of the company to process

    Returns:
        dict: Task information including task_id for status tracking
    """
    try:
        from domains.companies.repository import company_repository

        # Get company details
        company = company_repository.get_company_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found",
            )

        # Trigger company-specific task with "enriched" status to re-validate
        task = enrich_company_job_listings.delay(company_id, "enriched")

        return {
            "status": "task_started",
            "message": f"Task to revise job listings for {company.name} has been queued",
            "company_id": company_id,
            "company_name": company.name,
            "task_id": task.id,
            "instructions": "Check worker logs with: docker-compose logs -f worker",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
        )


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Check the status of a Celery task

    Possible states:
    - PENDING: Task is waiting for execution
    - STARTED: Task has been started
    - SUCCESS: Task executed successfully
    - FAILURE: Task execution failed
    - RETRY: Task is waiting to be retried

    - **task_id**: Celery task ID returned from task trigger endpoints
    """
    try:
        from celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task_result.state,
            "ready": task_result.ready(),
        }

        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.result)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check task status: {str(e)}",
        )


@router.post("/{task_id}/cancel", response_model=dict)
async def cancel_task(
    task_id: str,
    is_chain: bool = Query(False, description="Set to true if canceling a chain"),
):
    """
    Cancel/revoke a Celery task or chain of tasks

    This endpoint can cancel:
    - Individual tasks: Set is_chain=false (default)
    - Chain of tasks: Set is_chain=true

    When canceling a chain:
    - Revokes the chain task itself
    - Looks up child tasks in JobProcess repository by parent_instance_id
    - Revokes each child task in Celery
    - Releases all child task locks in the repository
    - Terminates any currently running tasks

    Args:
        task_id: Celery task ID or chain ID to cancel
        is_chain: Whether the task_id is a chain (default: false)

    Returns:
        dict: Cancellation status and details
    """
    try:
        from celery_app import celery_app

        if is_chain:
            # Cancel chain of tasks
            chain_result = celery_app.AsyncResult(task_id)

            # Revoke the chain task itself
            chain_result.revoke(terminate=True, signal="SIGKILL")

            cancelled_tasks = [task_id]
            locks_released = 0

            # Get child tasks from JobProcess repository using parent_instance_id
            child_tasks = job_process_repository.get_child_tasks(task_id)

            logger.info(
                f"Found {len(child_tasks)} child tasks for parent {task_id}",
                extra={
                    "context": "cancel_task",
                    "parent_task_id": task_id,
                    "child_count": len(child_tasks),
                },
            )

            # Revoke each child task in Celery
            for child_task in child_tasks:
                if child_task.task_instance_id:
                    try:
                        child_result = celery_app.AsyncResult(
                            child_task.task_instance_id
                        )
                        child_result.revoke(terminate=True, signal="SIGKILL")
                        cancelled_tasks.append(child_task.task_instance_id)

                        logger.info(
                            f"Revoked child task {child_task.task_name}",
                            extra={
                                "context": "cancel_task",
                                "child_task_id": child_task.task_instance_id,
                                "child_task_name": child_task.task_name,
                            },
                        )
                    except Exception as revoke_error:
                        logger.warning(
                            f"Failed to revoke child task {child_task.task_instance_id}: {str(revoke_error)}",
                            extra={
                                "context": "cancel_task",
                                "child_task_id": child_task.task_instance_id,
                                "error": str(revoke_error),
                            },
                        )

            # Also try to iterate through Celery chain results (for any tasks not tracked in repo)
            try:
                current = chain_result
                while current and not current.ready():
                    current.revoke(terminate=True, signal="SIGKILL")
                    current_id = str(current.id)
                    if current_id not in cancelled_tasks:
                        cancelled_tasks.append(current_id)

                    try:
                        if hasattr(current, "children") and current.children:
                            current = current.children[0]
                        else:
                            break
                    except (AttributeError, IndexError):
                        break

            except Exception as chain_error:
                logger.warning(
                    f"Error iterating Celery chain: {str(chain_error)}",
                    extra={"context": "cancel_task", "error": str(chain_error)},
                )

            return {
                "status": "cancelled",
                "message": f"Chain and {len(cancelled_tasks)} task(s) cancelled, {locks_released} lock(s) released",
                "task_id": task_id,
                "is_chain": True,
                "cancelled_tasks": cancelled_tasks,
                "child_tasks_from_repo": len(child_tasks),
                "locks_released": locks_released,
            }
        else:
            # Cancel individual task
            task_result = celery_app.AsyncResult(task_id)
            task_result.revoke(terminate=True, signal="SIGKILL")

            return {
                "status": "cancelled",
                "message": "Task cancelled successfully",
                "task_id": task_id,
                "is_chain": False,
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )
