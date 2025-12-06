"""
Routes for browser automation and job application filling
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import uuid
import base64
import os
import tempfile


from domains.candidates.repository import (
    candidate_repository,
    candidate_file_repository,
)
from domains.applications.repository import ApplicationRepository
from integrations.browser_automation import (
    ApplyToJobPostingAutomationParams,
    ApplyToJobPostingParams,
    apply_to_job_posting,
)

application_repository = ApplicationRepository()

router = APIRouter(prefix="/api/automation", tags=["automation"])


class JobApplicationRequest(BaseModel):
    """Request model for triggering job application automation"""

    candidate_id: str = Field(
        ..., description="Candidate ID to retrieve information from database"
    )
    application_id: Optional[str] = Field(
        None, description="Optional application ID to track"
    )


class JobApplicationResponse(BaseModel):
    """Response model for job application automation"""

    success: bool
    message: str
    application_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AutomationStatus(BaseModel):
    """Status model for automation jobs"""

    status: str  # "pending", "running", "completed", "failed"
    application_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


# In-memory storage for tracking automation jobs (use Redis/DB in production)
automation_jobs: Dict[str, AutomationStatus] = {}


def build_candidate_info_from_metadata(candidate) -> Dict[str, Any]:
    """
    Build candidate info dictionary from candidate metadata for automation

    Args:
        candidate: CandidateResponse object with metadata

    Returns:
        Dictionary formatted for job application automation
    """
    if not candidate.metadata or not candidate.metadata.categorization_schema:
        raise ValueError(
            "Candidate does not have parsed CV data (categorization_schema)"
        )

    schema = candidate.metadata.categorization_schema

    # Convert Pydantic model to dictionary
    return schema.model_dump()


async def run_automation_job(application_id: str, candidate_id: str):
    """Background task to run the automation job"""
    cv_file_path = None
    try:
        # Update status to running
        automation_jobs[application_id].status = "running"
        automation_jobs[application_id].started_at = datetime.now()

        # Fetch application with details to get job listing information
        application = application_repository.get_application_with_details(
            application_id
        )
        if not application:
            raise ValueError(f"Application with id {application_id} not found")

        # Get job listing URL
        if not application.job_listing or not application.job_listing.url:
            raise ValueError(
                f"No job listing URL found for application {application_id}"
            )

        job_listing_url = application.job_listing.url
        print(f"Applying to job at URL: {job_listing_url}")

        # Fetch candidate data
        candidate = candidate_repository.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate with id {candidate_id} not found")

        # Load the latest CV file from candidate_files collection
        latest_cv = candidate_file_repository.get_latest_cv_for_candidate(candidate_id)
        if not latest_cv:
            raise ValueError(f"No CV file found for candidate {candidate_id}")

        # Decode base64 CV data to bytes
        cv_bytes = base64.b64decode(latest_cv.file_data_base64)

        # Create a temporary file to store the PDF
        # Use suffix from original filename to preserve extension
        file_extension = os.path.splitext(latest_cv.file_name)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension, mode="wb"
        ) as temp_file:
            temp_file.write(cv_bytes)
            cv_file_path = temp_file.name

        print(f"Created temporary CV file at: {cv_file_path}")

        # Build candidate info from metadata
        candidate_info = build_candidate_info_from_metadata(candidate)

        automation_params = ApplyToJobPostingAutomationParams()

        # Pass CV file path and job listing URL to automation
        apply_info = ApplyToJobPostingParams(
            info=candidate_info,
            resume_file_path=cv_file_path,
            url_to_apply=job_listing_url,
        )

        # Run the automation
        result = await apply_to_job_posting(apply_info, automation_params)

        # Update status to completed
        automation_jobs[application_id].status = "completed"
        automation_jobs[application_id].completed_at = datetime.now()
        automation_jobs[application_id].result = result

    except Exception as e:
        # Update status to failed
        automation_jobs[application_id].status = "failed"
        automation_jobs[application_id].completed_at = datetime.now()
        automation_jobs[application_id].error = str(e)
        print(f"Automation job failed: {e}")

    finally:
        # Clean up temporary file
        if cv_file_path and os.path.exists(cv_file_path):
            try:
                os.remove(cv_file_path)
                print(f"Cleaned up temporary CV file: {cv_file_path}")
            except Exception as cleanup_error:
                print(f"Failed to clean up temporary file: {cleanup_error}")


@router.post("/apply", response_model=JobApplicationResponse)
async def trigger_job_application(
    request: JobApplicationRequest, background_tasks: BackgroundTasks
):
    """
    Trigger browser automation to fill out a job application form

    This endpoint starts the automation process in the background and returns immediately.
    Use the returned application_id to check the status of the automation job.

    Example request body:
    ```json
    {
        "candidate_id": "673f1234567890abcdef1234"
    }
    ```

    The candidate must have a parsed CV (metadata.categorization_schema) in the database.
    """
    try:
        # Validate candidate exists and has parsed CV data
        candidate = candidate_repository.get_candidate_by_id(request.candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate with id {request.candidate_id} not found",
            )

        if not candidate.metadata or not candidate.metadata.categorization_schema:
            raise HTTPException(
                status_code=400,
                detail="Candidate does not have parsed CV data. Please upload and parse a CV first.",
            )

        # Generate application ID if not provided
        application_id = request.application_id or f"app_{uuid.uuid4().hex[:8]}"

        # Initialize job status
        automation_jobs[application_id] = AutomationStatus(
            status="pending", application_id=application_id
        )

        # Add background task to run the automation
        background_tasks.add_task(
            run_automation_job, application_id, request.candidate_id
        )

        return JobApplicationResponse(
            success=True,
            message="Job application automation started successfully",
            application_id=application_id,
            status="pending",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start automation: {str(e)}"
        )


@router.get("/status/{application_id}", response_model=AutomationStatus)
async def get_automation_status(application_id: str):
    """
    Get the status of a running or completed automation job

    Returns the current status, start/completion times, and results if available.
    """
    if application_id not in automation_jobs:
        raise HTTPException(status_code=404, detail="Application ID not found")

    return automation_jobs[application_id]


@router.get("/jobs", response_model=Dict[str, AutomationStatus])
async def list_automation_jobs():
    """
    List all automation jobs and their statuses

    Returns a dictionary of all tracked automation jobs.
    """
    return automation_jobs


@router.delete("/jobs/{application_id}")
async def delete_automation_job(application_id: str):
    """
    Delete an automation job from the tracking system

    This only removes the job from memory, it doesn't stop a running automation.
    """
    if application_id not in automation_jobs:
        raise HTTPException(status_code=404, detail="Application ID not found")

    del automation_jobs[application_id]

    return {"success": True, "message": f"Job {application_id} deleted successfully"}


@router.post("/apply/sync", response_model=Dict[str, Any])
async def trigger_job_application_sync(request: JobApplicationRequest):
    """
    Trigger browser automation to fill out a job application form (synchronous)

    This endpoint waits for the automation to complete before returning.
    Use this for testing or when you need immediate results.

    ⚠️ Warning: This endpoint may take several minutes to complete.
    """
    cv_file_path = None
    try:
        # Validate candidate exists and has parsed CV data
        candidate = candidate_repository.get_candidate_by_id(request.candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate with id {request.candidate_id} not found",
            )

        if not candidate.metadata or not candidate.metadata.categorization_schema:
            raise HTTPException(
                status_code=400,
                detail="Candidate does not have parsed CV data. Please upload and parse a CV first.",
            )

        # Load the latest CV file from candidate_files collection
        latest_cv = candidate_file_repository.get_latest_cv_for_candidate(
            request.candidate_id
        )
        if not latest_cv:
            raise HTTPException(
                status_code=404,
                detail=f"No CV file found for candidate {request.candidate_id}",
            )

        # Decode base64 CV data to bytes
        cv_bytes = base64.b64decode(latest_cv.file_data_base64)

        # Create a temporary file to store the PDF
        file_extension = os.path.splitext(latest_cv.file_name)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension, mode="wb"
        ) as temp_file:
            temp_file.write(cv_bytes)
            cv_file_path = temp_file.name

        print(f"Created temporary CV file at: {cv_file_path}")

        # Generate application ID if not provided
        application_id = request.application_id or f"app_{uuid.uuid4().hex[:8]}"

        # Fetch application with details to get job listing information
        if request.application_id:
            application = application_repository.get_application_with_details(
                request.application_id
            )
            if not application:
                raise HTTPException(
                    status_code=404,
                    detail=f"Application with id {request.application_id} not found",
                )

            # Get job listing URL
            if not application.job_listing or not application.job_listing.url:
                raise HTTPException(
                    status_code=400,
                    detail=f"No job listing URL found for application {request.application_id}",
                )

            job_listing_url = application.job_listing.url
            print(f"Applying to job at URL: {job_listing_url}")
        else:
            # If no application_id provided, use default URL
            job_listing_url = "https://careers.deliveroo.co.uk/role/head-of-smb-deliveroo-for-work-632de4408c2e/"
            print(f"No application ID provided, using default URL: {job_listing_url}")

        # Build candidate info from metadata
        candidate_info = build_candidate_info_from_metadata(candidate)

        params = ApplyToJobPostingAutomationParams(headless=False)

        # Pass CV file path and job listing URL to automation
        apply_info = ApplyToJobPostingParams(
            info=candidate_info,
            resume_file_path=cv_file_path,
            url_to_apply=job_listing_url,
        )

        # Run the automation synchronously
        result = await apply_to_job_posting(apply_info, params=params)

        return {
            "success": True,
            "application_id": application_id,
            "result": result,
            "timestamp": datetime.now(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")
    finally:
        # Clean up temporary file
        if cv_file_path and os.path.exists(cv_file_path):
            try:
                os.remove(cv_file_path)
                print(f"Cleaned up temporary CV file: {cv_file_path}")
            except Exception as cleanup_error:
                print(f"Failed to clean up temporary file: {cleanup_error}")
