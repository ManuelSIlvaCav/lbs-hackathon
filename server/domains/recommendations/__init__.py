"""
Recommendations Domain
Contains models, repository, service, and routes for job recommendations
"""

from .models import (
    RecommendationModel,
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatus,
)
from .repository import recommendation_repository
from .service import recommendation_service
from .routes import router

__all__ = [
    "RecommendationModel",
    "RecommendationCreate",
    "RecommendationResponse",
    "RecommendationStatus",
    "recommendation_repository",
    "recommendation_service",
    "router",
]
