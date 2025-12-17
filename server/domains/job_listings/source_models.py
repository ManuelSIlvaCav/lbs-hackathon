"""
Models for job listing sources - tracking jobs from multiple providers
"""

from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId

from domains.job_listings.models import JobListingMetadata


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class ApolloProviderSourceInfo(BaseModel):
    """Information about a job from a specific provider"""

    job_enrichment_id: Optional[str] = Field(
        default=None, description="Reference to the job enrichment document"
    )
    provider_job_id: str = Field(..., description="The job ID from the provider")
    url: Optional[str] = Field(default=None, description="URL from this provider")
    first_seen_at: datetime = Field(
        default_factory=datetime.now,
        description="When this source was first discovered",
    )
    last_seen_at: datetime = Field(
        default_factory=datetime.now, description="When this source was last updated"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class JobListingSourceFieldModel(BaseModel):
    apollo: Optional[ApolloProviderSourceInfo] = None
    job_listing_agent: Optional[JobListingMetadata] = None


class JobListingSourceModel(BaseModel):
    """Model for tracking a job listing across multiple sources/providers"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    job_listing_id: PyObjectId = Field(
        ..., description="Reference to the main job_listing document (ObjectId)"
    )
    company_id: PyObjectId = Field(
        ..., description="Reference to the company document (ObjectId)"
    )
    sources: JobListingSourceFieldModel = Field(
        default_factory=JobListingSourceFieldModel,
        description="Sources information for the job listing",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class JobListingSourceCreate(BaseModel):
    """Model for creating a job listing source tracking document"""

    job_listing_id: PyObjectId
    company_id: PyObjectId
    sources: JobListingSourceFieldModel = Field(
        default_factory=JobListingSourceFieldModel,
    )


class JobListingSourceUpdate(BaseModel):
    """Model for updating job listing sources"""

    sources: Optional[JobListingSourceFieldModel] = None


class JobListingSourceResponse(BaseModel):
    """Model for job listing source response"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
    )

    id: str = Field(alias="_id")
    job_listing_id: PyObjectId
    company_id: PyObjectId
    sources: JobListingSourceFieldModel
    created_at: datetime
    updated_at: datetime
