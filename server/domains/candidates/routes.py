"""
API routes for candidate operations
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
import os
import tempfile

from .models import CandidateCreate, CandidateUpdate, CandidateResponse
from .repository import candidate_repository
from domains.auth.routes import get_current_active_user
from domains.auth.models import UserInDB


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(candidate: CandidateCreate):
    """
    Create a new candidate

    - **name**: Candidate's full name (required)
    - **email**: Candidate's email address (optional)
    """
    try:
        return candidate_repository.create_candidate(candidate)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate: {str(e)}",
        )


@router.get("/", response_model=List[CandidateResponse])
async def get_candidates(skip: int = 0, limit: int = 100):
    """
    Get all candidates with pagination

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    return candidate_repository.get_all_candidates(skip=skip, limit=limit)


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Get a specific candidate by ID

    Requires authentication. Users can only access their own candidate profile.

    - **candidate_id**: MongoDB ObjectId as string
    """
    # Validate that the user is accessing their own candidate profile
    if current_user.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile",
        )

    candidate = candidate_repository.get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    candidate: CandidateUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Update a candidate

    Requires authentication. Users can only update their own candidate profile.

    - **candidate_id**: MongoDB ObjectId as string
    - **name**: Updated candidate name (optional)
    - **email**: Updated candidate email (optional)
    - **metadata**: Updated candidate metadata including CV data (optional)
    """
    # Validate that the user is updating their own candidate profile
    if current_user.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    updated_candidate = candidate_repository.update_candidate(candidate_id, candidate)
    if not updated_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found or update failed",
        )
    return updated_candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(candidate_id: str):
    """
    Delete a candidate

    - **candidate_id**: MongoDB ObjectId as string
    """
    success = candidate_repository.delete_candidate(candidate_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )
    return None


@router.get("/stats/count")
async def get_candidate_count():
    """
    Get total count of candidates
    """
    count = candidate_repository.get_candidate_count()
    return {"count": count}


@router.post("/{candidate_id}/upload-cv", response_model=CandidateResponse)
async def upload_and_parse_cv(
    candidate_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Upload a CV file for a candidate and parse it using the CV parser agent

    Requires authentication. Users can only upload CVs for their own candidate profile.

    - **candidate_id**: MongoDB ObjectId as string
    - **file**: CV file (PDF, DOC, DOCX, TXT, RTF)

    The CV will be parsed and the categorization schema will be saved to the candidate's metadata.
    """
    # Validate that the user is uploading to their own candidate profile
    if current_user.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload CVs to your own profile",
        )

    # Validate candidate exists
    candidate = candidate_repository.get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    # Validate file type
    allowed_extensions = {".pdf", ".doc", ".docx", ".txt", ".rtf"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
        )

    # Save uploaded file temporarily
    temp_file = None
    try:
        # Create a temporary file with the same extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            # Read and write file content
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        print(f"Temporary CV file saved at: {temp_file_path}")
        # Parse the CV using the repository function
        updated_candidate = await candidate_repository.parse_cv(
            candidate_id=candidate_id, cv_file_path=temp_file_path
        )

        if not updated_candidate:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse CV or update candidate",
            )

        return updated_candidate

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV: {str(e)}",
        )
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Warning: Failed to delete temporary file {temp_file_path}: {e}")
