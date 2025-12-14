"""
API routes for job listing operations
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
import asyncio

from .models import (
    JobListingCreate,
    JobListingUpdate,
    JobListingModel,
    PaginatedJobListingResponse,
    JobListingOrigin,
)
from .repository import job_listing_repository
from .tasks import (
    revise_all_companies_enriched_jobs,
    revise_company_enriched_jobs,
    cleanup_stale_job_processes,
)
from .process_repository import job_process_repository
from .categories import (
    get_all_profile_categories,
    get_all_role_titles,
)


router = APIRouter(prefix="/api/job-listings", tags=["job-listings"])


@router.post("/", response_model=JobListingModel, status_code=status.HTTP_201_CREATED)
async def create_job_listing(job_listing: JobListingCreate):
    """
    Create a new job listing with automatic scraping and AI parsing

    This endpoint may take up to 90 seconds due to:
    - Web scraping with Playwright (up to 60s)
    - AI parsing of job description (up to 30s)

    - **url**: Job listing URL (required)
    - **title**: Job title (optional)
    - **company**: Company name (optional)
    - **location**: Job location (optional)
    - **description**: Job description (optional)

    Note: The URL will be automatically scraped and parsed using AI
    to extract structured job information (requirements, skills, etc.)
    """
    try:
        # Create task with extended timeout for scraping + parsing
        result = await asyncio.wait_for(
            job_listing_repository.create_job_listing(job_listing),
            timeout=120.0,  # 120 seconds total timeout (scraping + parsing)
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Job listing creation timed out. The scraping or parsing took too long. Please try again.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job listing: {str(e)}",
        )


@router.get("/", response_model=List[JobListingModel])
async def get_job_listings(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """
    Get all job listings with pagination and optional status filter

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    - **status**: Optional status filter ("active", "archived", etc.)
    """
    return job_listing_repository.get_all_job_listings(
        skip=skip, limit=limit, status=status_filter
    )


@router.get("/search", response_model=PaginatedJobListingResponse)
async def search_job_listings(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    country: Optional[str] = Query(None, description="Filter by country"),
    city: Optional[str] = Query(None, description="Filter by city"),
    origin: Optional[str] = Query(
        None, description="Filter by origin (linkedin, greenhouse, workday, careers)"
    ),
    profile_category: Optional[str] = Query(
        None, description="Filter by profile category"
    ),
    role_title: Optional[str] = Query(None, description="Filter by role title"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
):
    """
    Search job listings with filters using efficient aggregation pipeline pagination

    This endpoint uses MongoDB aggregation with $facet for optimal performance.
    Results are sorted by most recent first (created_at descending).

    - **company_id**: Filter by company ID
    - **country**: Filter by country
    - **city**: Filter by city
    - **origin**: Filter by origin (linkedin, greenhouse, workday, careers)
    - **profile_category**: Filter by profile category
    - **role_title**: Filter by role title
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 100)

    Returns paginated response with items, total count, skip, limit, and has_more flag.
    """
    try:
        items, total = job_listing_repository.search_job_listings(
            company_id=company_id,
            country=country,
            city=city,
            origin=origin,
            profile_category=profile_category,
            role_title=role_title,
            skip=skip,
            limit=limit,
        )

        has_more = (skip + limit) < total

        return PaginatedJobListingResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search job listings: {str(e)}",
        )


@router.get("/search-options", response_model=dict)
async def get_search_options():
    """
    Get all available search filter options for job listings

    Returns all distinct values for:
    - origins: Job sources (linkedin, greenhouse, workday, careers)
    - profile_categories: Job profile categories
    - role_titles: Specific role titles (flat list for backward compatibility)
    - role_titles_by_category: Role titles organized by profile category

    This endpoint is used to populate search filter dropdowns in the frontend.

    Returns:
        dict: Object containing arrays of available filter options
    """
    try:
        from .categories import PROFILE_CATEGORIES

        # Get all profile categories
        profile_categories = get_all_profile_categories()

        # Get all role titles (already sorted and deduplicated)
        role_titles = get_all_role_titles()

        # Get all origins from enum
        origins = [origin.value for origin in JobListingOrigin]

        # Get role titles organized by category
        role_titles_by_category = {
            category: sorted(roles) for category, roles in PROFILE_CATEGORIES.items()
        }

        return {
            "origins": origins,
            "profile_categories": sorted(profile_categories),
            "role_titles": role_titles,
            "role_titles_by_category": role_titles_by_category,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch search options: {str(e)}",
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
        task = revise_all_companies_enriched_jobs.delay()

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

        # Trigger company-specific task
        task = revise_company_enriched_jobs.delay(company_id, company.name)

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


@router.post("/cleanup-stale-processes", response_model=dict)
async def trigger_cleanup_stale_processes(hours: int = 2):
    """
    Trigger cleanup of stale job process locks

    This endpoint triggers a task to clean up locks from jobs that have been
    processing for too long (likely due to crashes or hung processes).

    Args:
        hours: Number of hours after which a lock is considered stale (default: 2)

    Returns:
        dict: Task information including task_id
    """
    try:
        task = cleanup_stale_job_processes.delay(hours=hours)

        return {
            "status": "task_started",
            "message": f"Cleanup task queued for locks older than {hours} hours",
            "task_id": task.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger cleanup: {str(e)}",
        )


@router.get("/task-status/{task_name}", response_model=dict)
async def get_task_status(task_name: str):
    """
    Get the current processing status/lock for a task

    Args:
        task_name: Name of the task (e.g., 'revise_enriched_job_listings')

    Returns:
        dict: Lock status information or None if no lock exists
    """
    try:
        lock_status = job_process_repository.get_lock_status(task_name)

        if lock_status:
            return {
                "has_lock": True,
                "task_name": lock_status.task_name,
                "task_instance_id": lock_status.task_instance_id,
                "status": lock_status.status,
                "started_at": lock_status.started_at.isoformat(),
                "completed_at": (
                    lock_status.completed_at.isoformat()
                    if lock_status.completed_at
                    else None
                ),
                "error_message": lock_status.error_message,
                "retry_count": lock_status.retry_count,
            }
        else:
            return {
                "has_lock": False,
                "task_name": task_name,
                "message": "No active or recent task found",
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.get("/{job_listing_id}", response_model=JobListingModel)
async def get_job_listing(job_listing_id: str):
    """
    Get a specific job listing by ID

    - **job_listing_id**: MongoDB ObjectId as string
    """
    job_listing = job_listing_repository.get_job_listing_by_id(job_listing_id)
    if not job_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with id {job_listing_id} not found",
        )
    return job_listing


@router.put("/{job_listing_id}", response_model=JobListingModel)
async def update_job_listing(job_listing_id: str, job_listing: JobListingUpdate):
    """
    Update a job listing

    - **job_listing_id**: MongoDB ObjectId as string
    - **url**: Updated URL (optional)
    - **title**: Updated title (optional)
    - **company**: Updated company (optional)
    - **location**: Updated location (optional)
    - **description**: Updated description (optional)
    - **status**: Updated status (optional)
    """
    updated_job = job_listing_repository.update_job_listing(job_listing_id, job_listing)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with id {job_listing_id} not found or update failed",
        )
    return updated_job


@router.delete("/{job_listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_listing(job_listing_id: str):
    """
    Delete a job listing

    - **job_listing_id**: MongoDB ObjectId as string
    """
    success = job_listing_repository.delete_job_listing(job_listing_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job listing with id {job_listing_id} not found",
        )
    return None


@router.post("/{job_listing_id}/enrich", response_model=JobListingModel)
async def enrich_job_listing(job_listing_id: str):
    """
    Enrich a job listing by running the AI agent to extract structured data

    This endpoint:
    - Scrapes the job description from the URL
    - Runs AI agent to extract profile_categories, role_titles, employment_type, work_arrangement
    - Extracts detailed requirements (minimum/preferred, skills, experience, etc.)
    - Updates the job listing with enriched metadata
    - Sets source_status to 'enriched'

    May take up to 90 seconds due to scraping and AI processing.

    - **job_listing_id**: MongoDB ObjectId as string
    """
    try:
        # Enrich with extended timeout
        result = await asyncio.wait_for(
            job_listing_repository.enrich_job_listing(job_listing_id),
            timeout=120.0,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job listing with id {job_listing_id} not found or enrichment failed",
            )

        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Job listing enrichment timed out. Please try again.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich job listing: {str(e)}",
        )


@router.get("/tasks/{task_id}/status")
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


@router.post("/tasks/{task_id}/cancel", response_model=dict)
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
    - Iterates through all tasks in the chain
    - Revokes each task individually
    - Terminates any currently running tasks

    Args:
        task_id: Celery task ID or chain ID to cancel
        is_chain: Whether the task_id is a chain (default: false)

    Returns:
        dict: Cancellation status and details
    """
    try:
        from celery_app import celery_app
        from celery.result import AsyncResult

        if is_chain:
            # Cancel chain of tasks
            chain_result = celery_app.AsyncResult(task_id)

            # Revoke the chain task itself
            chain_result.revoke(terminate=True, signal="SIGKILL")

            cancelled_tasks = [task_id]

            # For chains, we need to get and revoke all child tasks
            # In Celery 5+, chains store results as parent-child relationships
            try:
                # Try to iterate through the chain results
                current = chain_result
                while current and not current.ready():
                    # Revoke the current task
                    current.revoke(terminate=True, signal="SIGKILL")
                    cancelled_tasks.append(str(current.id))

                    # Move to the next task in the chain
                    # In Celery 5+, chains use the result as parent for the next task
                    try:
                        if hasattr(current, "children") and current.children:
                            current = current.children[0]
                        else:
                            break
                    except (AttributeError, IndexError):
                        break

            except Exception as chain_error:
                # If we can't iterate the chain, at least we revoked the main chain task
                pass

            return {
                "status": "cancelled",
                "message": f"Chain and {len(cancelled_tasks)} task(s) cancelled",
                "task_id": task_id,
                "is_chain": True,
                "cancelled_tasks": cancelled_tasks,
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
