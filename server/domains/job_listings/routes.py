"""
API routes for job listing operations
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
import asyncio

from .models import JobListingCreate, JobListingUpdate, JobListingModel
from .repository import job_listing_repository


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
