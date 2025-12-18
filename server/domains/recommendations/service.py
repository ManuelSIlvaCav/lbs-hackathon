"""
Service layer for recommendations
Handles business logic and orchestrates repository operations
"""

import logging
from typing import List, Optional

from .models import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatus,
)
from .repository import recommendation_repository

logger = logging.getLogger("app")


class RecommendationService:
    """Service for recommendation business logic"""

    def __init__(self):
        self.repository = recommendation_repository

    def create_recommendation(
        self, recommendation_data: RecommendationCreate
    ) -> RecommendationResponse:
        """
        Create a single recommendation
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendation_data: RecommendationCreate object

        Returns:
            RecommendationResponse object
        """
        return self.repository.create_recommendation(recommendation_data)

    def create_recommendations_bulk(
        self, recommendations_data: List[RecommendationCreate]
    ) -> tuple[List[str], int]:
        """
        Create multiple recommendations in bulk
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendations_data: List of RecommendationCreate objects

        Returns:
            Tuple of (list of inserted IDs, count of skipped duplicates)
        """
        return self.repository.create_recommendations_bulk(recommendations_data)

    def get_recommendation(
        self, recommendation_id: str
    ) -> Optional[RecommendationResponse]:
        """
        Get a single recommendation by ID
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendation_id: Recommendation ID

        Returns:
            RecommendationResponse if found, None otherwise
        """
        return self.repository.get_recommendation(recommendation_id)

    def get_recommendations(
        self,
        candidate_id: Optional[str] = None,
        job_listing_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[RecommendationStatus] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[RecommendationResponse]:
        """
        Get recommendations with optional filters
        Currently just calls repository, placeholder for future business logic

        Args:
            candidate_id: Filter by candidate ID
            job_listing_id: Filter by job listing ID
            company_id: Filter by company ID
            status: Filter by recommendation status
            limit: Maximum number of results
            skip: Number of results to skip (pagination)

        Returns:
            List of RecommendationResponse objects
        """
        return self.repository.get_recommendations(
            candidate_id=candidate_id,
            job_listing_id=job_listing_id,
            company_id=company_id,
            status=status,
            limit=limit,
            skip=skip,
        )

    def update_recommendation_status(
        self, recommendation_id: str, status: RecommendationStatus
    ) -> Optional[RecommendationResponse]:
        """
        Update recommendation status
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendation_id: Recommendation ID
            status: New status

        Returns:
            Updated RecommendationResponse if successful, None otherwise
        """
        return self.repository.update_recommendation_status(recommendation_id, status)

    def soft_delete_recommendation(
        self, recommendation_id: str
    ) -> Optional[RecommendationResponse]:
        """
        Soft delete a recommendation
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendation_id: Recommendation ID

        Returns:
            Updated RecommendationResponse if successful, None otherwise
        """
        return self.repository.soft_delete_recommendation(recommendation_id)

    def delete_recommendation(self, recommendation_id: str) -> bool:
        """
        Permanently delete a recommendation
        Currently just calls repository, placeholder for future business logic

        Args:
            recommendation_id: Recommendation ID

        Returns:
            True if deletion was successful, False otherwise
        """
        return self.repository.delete_recommendation(recommendation_id)

    def get_recommendations_with_details(
        self,
        candidate_id: Optional[str] = None,
        job_listing_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[RecommendationStatus] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> dict:
        """
        Get recommendations with full job listing and company details
        Currently just calls repository, placeholder for future business logic

        Args:
            candidate_id: Filter by candidate ID
            job_listing_id: Filter by job listing ID
            company_id: Filter by company ID
            status: Filter by recommendation status
            limit: Maximum number of results
            skip: Number of results to skip (pagination)

        Returns:
            Dict with paginated recommendations including job and company details
        """
        return self.repository.get_recommendations_with_details(
            candidate_id=candidate_id,
            job_listing_id=job_listing_id,
            company_id=company_id,
            status=status,
            limit=limit,
            skip=skip,
        )


# Singleton instance
recommendation_service = RecommendationService()
