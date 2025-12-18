"""
API routes for recommendation operations
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
import logging

from .models import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatus,
)
from .service import recommendation_service

logger = logging.getLogger("app")

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post(
    "/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED
)
async def create_recommendation(recommendation: RecommendationCreate):
    """
    Create a new recommendation

    - **candidate_id**: Candidate ObjectId (required)
    - **job_listing_id**: Job listing ObjectId (required)
    - **company_id**: Company ObjectId (required)
    - **reason**: Reason for recommendation (optional)
    - **recommendation_status**: Status (default: pending)
    """
    try:
        return recommendation_service.create_recommendation(recommendation)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recommendation: {str(e)}",
        )


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_recommendations_bulk(recommendations: List[RecommendationCreate]):
    """
    Create multiple recommendations in bulk

    Returns:
    - **inserted_ids**: List of successfully inserted recommendation IDs
    - **skipped_count**: Number of duplicate recommendations skipped
    """
    try:
        inserted_ids, skipped = recommendation_service.create_recommendations_bulk(
            recommendations
        )
        return {
            "inserted_ids": inserted_ids,
            "inserted_count": len(inserted_ids),
            "skipped_count": skipped,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recommendations: {str(e)}",
        )


@router.get("/", response_model=dict)
async def get_recommendations(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    job_listing_id: Optional[str] = Query(None, description="Filter by job listing ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (pending, recommended, viewed, applied, rejected, deleted)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
):
    """
    Get recommendations with filters and pagination
    Includes populated job listing and company information

    Returns paginated response with:
    - **items**: List of recommendations with full job and company details
    - **total**: Total count of matching recommendations
    - **skip**: Current skip value
    - **limit**: Current limit value
    - **has_more**: Whether more results are available
    """
    try:
        # Parse status enum if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = RecommendationStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status value. Must be one of: {', '.join([s.value for s in RecommendationStatus])}",
                )

        # Get recommendations with populated data
        result = recommendation_service.get_recommendations_with_details(
            candidate_id=candidate_id,
            job_listing_id=job_listing_id,
            company_id=company_id,
            status=status_enum,
            limit=limit,
            skip=skip,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}",
        )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(recommendation_id: str):
    """
    Get a single recommendation by ID
    """
    try:
        recommendation = recommendation_service.get_recommendation(recommendation_id)
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )
        return recommendation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation: {str(e)}",
        )


@router.patch("/{recommendation_id}/status")
async def update_recommendation_status(
    recommendation_id: str,
    status_value: str = Query(
        ...,
        alias="status",
        description="New status (pending, recommended, viewed, applied, rejected)",
    ),
):
    """
    Update recommendation status
    """
    try:
        # Parse status enum
        try:
            status_enum = RecommendationStatus(status_value.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value. Must be one of: {', '.join([s.value for s in RecommendationStatus])}",
            )

        updated = recommendation_service.update_recommendation_status(
            recommendation_id, status_enum
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )
        return updated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recommendation status: {str(e)}",
        )


@router.delete("/{recommendation_id}")
async def soft_delete_recommendation(recommendation_id: str):
    """
    Soft delete a recommendation (marks as deleted)
    """
    try:
        deleted = recommendation_service.soft_delete_recommendation(recommendation_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )
        return {"message": "Recommendation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recommendation: {str(e)}",
        )
