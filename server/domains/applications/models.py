from typing import Annotated, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId

from domains.candidates.models import CandidateResponse
from domains.job_listings.models import JobListingResponse


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class ApplicationModel(BaseModel):
    """Model for job application data"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    job_listing_id: str = Field(..., description="ID of the job listing")
    candidate_id: str = Field(..., description="ID of the candidate")
    accuracy_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Accuracy score of the application (0-100)",
    )
    scoring_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed scoring breakdown from accuracy scoring agent",
    )
    status: str = Field(default="pending", description="Status of the application")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ApplicationCreate(BaseModel):
    """Model for creating a new application"""

    job_listing_id: str = Field(..., description="ID of the job listing")
    candidate_id: str = Field(..., description="ID of the candidate")
    accuracy_score: Optional[float] = Field(
        default=None, ge=0, le=100, description="Accuracy score (0-100)"
    )
    scoring_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed scoring breakdown from accuracy scoring agent",
    )
    status: str = Field(default="pending", description="Status of the application")


class ApplicationUpdate(BaseModel):
    """Model for updating an application"""

    accuracy_score: Optional[float] = Field(
        default=None, ge=0, le=100, description="Accuracy score (0-100)"
    )
    status: Optional[str] = Field(default=None, description="Status of the application")


class ApplicationResponse(BaseModel):
    """Model for application response with basic data"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    job_listing_id: str
    candidate_id: str
    accuracy_score: Optional[float] = None
    scoring_metadata: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ApplicationWithDetailsResponse(BaseModel):
    """Model for application response with joined job listing and candidate data"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    job_listing_id: str
    candidate_id: str
    accuracy_score: Optional[float] = None
    scoring_metadata: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    # Joined data
    job_listing: Optional[JobListingResponse] = None
    candidate: Optional[CandidateResponse] = None
