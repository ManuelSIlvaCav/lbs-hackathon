"""
Models for recommendation data
"""

from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId
from enum import Enum


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class RecommendationStatus(str, Enum):
    """Status of a recommendation"""

    PENDING = "pending"
    RECOMMENDED = "recommended"
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    DELETED = "deleted"


class RecommendationModel(BaseModel):
    """Model for recommendation data"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
        use_enum_values=True,
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    candidate_id: PyObjectId = Field(
        ..., description="Reference to candidate document (ObjectId)"
    )
    job_listing_id: PyObjectId = Field(
        ..., description="Reference to job_listing document (ObjectId)"
    )
    company_id: PyObjectId = Field(
        ..., description="Reference to company document (ObjectId)"
    )
    reason: Optional[str] = Field(
        default=None, description="Reason for the recommendation"
    )
    recommendation_status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING, description="Status of the recommendation"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    recommended_at: Optional[datetime] = Field(
        default=None, description="When recommendation was sent to candidate"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="When recommendation was soft deleted"
    )


class RecommendationCreate(BaseModel):
    """Model for creating a recommendation"""

    candidate_id: PyObjectId
    job_listing_id: PyObjectId
    company_id: PyObjectId
    reason: Optional[str] = None
    recommendation_status: RecommendationStatus = RecommendationStatus.PENDING


class RecommendationUpdate(BaseModel):
    """Model for updating a recommendation"""

    reason: Optional[str] = None
    recommendation_status: Optional[RecommendationStatus] = None
    recommended_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class RecommendationResponse(BaseModel):
    """Model for recommendation response"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
    )

    id: str = Field(alias="_id")
    candidate_id: PyObjectId
    job_listing_id: PyObjectId
    company_id: PyObjectId
    reason: Optional[str] = None
    recommendation_status: RecommendationStatus
    created_at: datetime
    recommended_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
