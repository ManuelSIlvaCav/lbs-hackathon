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
from .tasks import test_print_company_jobs
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
    - role_titles: Specific role titles

    This endpoint is used to populate search filter dropdowns in the frontend.

    Returns:
        dict: Object containing arrays of available filter options
    """
    try:
        # Get all profile categories
        profile_categories = get_all_profile_categories()

        # Get all role titles (already sorted and deduplicated)
        role_titles = get_all_role_titles()

        # Get all origins from enum
        origins = [origin.value for origin in JobListingOrigin]

        return {
            "origins": origins,
            "profile_categories": sorted(profile_categories),
            "role_titles": role_titles,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch search options: {str(e)}",
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


@router.post("/company/{company_id}/test-print-jobs")
async def test_print_company_jobs_route(company_id: str):
    """
    Test endpoint that triggers a Celery task to retrieve and print all job listings for a company

    This is a demonstration of Celery task integration. The task will:
    - Retrieve all job listings for the specified company
    - Print details of each job to the worker console logs
    - Return task ID for status tracking

    Check worker logs with: `docker-compose logs -f worker`

    - **company_id**: MongoDB ObjectId as string for the company
    """
    try:
        # Trigger the Celery task
        task = test_print_company_jobs.delay(company_id)

        return {
            "status": "task_started",
            "message": f"Task to print job listings for company {company_id} has been queued",
            "task_id": task.id,
            "company_id": company_id,
            "instructions": "Check worker logs with: docker-compose logs -f worker",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
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
