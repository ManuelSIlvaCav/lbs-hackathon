"""
API routes for application operations
"""

import asyncio
import random
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from models.applications import ApplicationWithDetailsResponse
from repositories.applications import application_repository
from repositories.candidates import candidate_repository
from repositories.job_listings import job_listing_repository
from integrations.agents.accuracy_scoring_agent import run_agent_accuracy_scoring


router = APIRouter(prefix="/api/applications", tags=["applications"])


class RecommendationRequest(BaseModel):
    """Request model for generating recommendations"""

    candidate_id: str = Field(
        ..., description="ID of the candidate to generate recommendations for"
    )


async def ai_recommendation(
    candidate_profile: Dict[str, Any], job_listings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    AI-powered recommendation system to match candidates with job listings using accuracy scoring agent.

    Args:
        candidate_profile: Dictionary containing candidate information and CV data
        job_listings: List of job listing dictionaries

    Returns:
        List of dictionaries with job_listing_id and accuracy_score
    """

    async def score_single_job(job: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single job listing against the candidate profile"""
        try:
            job_id = job.get("id", "unknown")
            print(f"Scoring job {job_id} for candidate {candidate_profile.get('id')}")

            # Extract the categorization schema from the job metadata
            job_metadata = job.get("metadata", {})
            categorization_schema = job_metadata.get("categorization_schema", {})

            # Skip if no categorization schema available
            if not categorization_schema:
                print(f"No categorization schema for job {job_id}, skipping")
                return None

            # Run the accuracy scoring agent
            scoring_result = await run_agent_accuracy_scoring(
                cv_json=candidate_profile, job_json=categorization_schema
            )

            if scoring_result and scoring_result.overall_match_score is not None:
                return {
                    "job_listing_id": job_id,
                    "accuracy_score": int(scoring_result.overall_match_score),
                    "scoring_metadata": scoring_result.model_dump(),  # Save full scoring details
                }
            else:
                print(f"No scoring result for job {job_id}, skipping")
                return None

        except Exception as e:
            print(f"Error scoring job {job.get('id', 'unknown')}: {e}")
            return None

    # Process all jobs concurrently
    scoring_tasks = [score_single_job(job) for job in job_listings]
    results = await asyncio.gather(*scoring_tasks)

    # Filter out None results and return valid scores
    return [result for result in results if result is not None]


@router.get("/", response_model=List[ApplicationWithDetailsResponse])
async def get_applications(
    candidate_id: str = Query(..., description="Filter by candidate ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    include_details: bool = Query(True, description="Include job listing details"),
):
    """
    Get all applications filtered by candidate ID

    - **candidate_id**: ID of the candidate (required query parameter)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    - **include_details**: Include full job listing details (default: true)

    Returns all applications for the specified candidate with job listing details.
    """
    return application_repository.get_applications_by_candidate(
        candidate_id=candidate_id,
        skip=skip,
        limit=limit,
        include_details=include_details,
    )


@router.post(
    "/recommendation",
    response_model=List[ApplicationWithDetailsResponse],
)
async def create_recommendations(request: RecommendationRequest):
    """
    Generate AI-powered job recommendations for a candidate and create applications.

    This endpoint:
    1. Fetches the candidate profile
    2. Fetches all active job listings
    3. Uses AI to match candidate with jobs (accuracy_score > 50)
    4. Creates applications for matching jobs

    - **candidate_id**: ID of the candidate to generate recommendations for (in request body)

    Returns list of created applications with job listing and candidate details.
    """
    # Fetch candidate profile
    candidate = candidate_repository.get_candidate_by_id(request.candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {request.candidate_id} not found",
        )

    # Get job listings the candidate has already applied to
    applied_job_ids = application_repository.get_applied_job_listing_ids(
        request.candidate_id
    )

    # Fetch all active job listings
    job_listings = job_listing_repository.get_all_job_listings(
        skip=0, limit=1000, status="active"  # Get all active jobs
    )

    if not job_listings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active job listings found"
        )

    # Filter out job listings the candidate has already applied to
    available_job_listings = [
        job for job in job_listings if job.id not in applied_job_ids
    ]

    if not available_job_listings:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="No new job listings available. Candidate has already applied to all active jobs.",
        )

    # Convert to dict format for AI recommendation
    candidate_dict = candidate.model_dump()
    job_listings_dict = [job.model_dump() for job in available_job_listings]

    print(f"Candidate dict: {job_listings_dict}")
    # Get AI recommendations (returns list of {job_listing_id, accuracy_score})
    # This runs async and processes all jobs concurrently
    recommendations = await ai_recommendation(candidate_dict, job_listings_dict)

    # Filter recommendations with accuracy > 50
    matching_recommendations = [
        rec for rec in recommendations if rec.get("accuracy_score", 0) > 0
    ]

    if not matching_recommendations:
        return []

    # Create applications for each matching recommendation
    created_applications = []
    skipped_count = 0

    for rec in matching_recommendations:
        try:
            from models.applications import ApplicationCreate

            app_data = ApplicationCreate(
                job_listing_id=rec["job_listing_id"],
                candidate_id=request.candidate_id,
                accuracy_score=rec["accuracy_score"],
                scoring_metadata=rec.get("scoring_metadata"),
                status="pending",
            )

            created_app = application_repository.create_application(app_data)
            created_applications.append(created_app)

        except ValueError as e:
            # Skip if application already exists or other validation error
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print(f"Duplicate application skipped: {error_msg}")
                skipped_count += 1
            else:
                print(f"Validation error, skipping application: {e}")
            continue
        except Exception as e:
            print(f"Error creating application: {e}")
            continue

    print(
        f"Created {len(created_applications)} applications, skipped {skipped_count} duplicates"
    )
    return created_applications


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: str,
    new_status: str = Query(..., alias="status", description="New status value"),
):
    """
    Update the status of an application

    - **application_id**: MongoDB ObjectId as string
    - **status**: New status value (e.g., "applied", "rejected", "pending")

    Returns the updated application with job listing and candidate details.
    """
    updated_app = application_repository.update_application_status(
        application_id, new_status
    )
    if not updated_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with id {application_id} not found or update failed",
        )
    return updated_app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: str):
    """
    Delete an application

    - **application_id**: MongoDB ObjectId as string

    Permanently removes the application from the database.
    """
    success = application_repository.delete_application(application_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with id {application_id} not found",
        )
    return None
