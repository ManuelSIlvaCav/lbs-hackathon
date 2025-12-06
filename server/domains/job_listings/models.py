"""
Models for job listing data
"""

from typing import Annotated, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId

from integrations.agents.job_listing_parser_agent import AgentJobCategorizationSchema


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class JobListingMetadata(BaseModel):
    """Metadata for job listing including parsed job description"""

    categorization_schema: Optional[AgentJobCategorizationSchema] = Field(
        default=None, description="Parsed job data from AgentJobCategorizationSchema"
    )


class JobListingModel(BaseModel):
    """Model for job listing data"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    url: str = Field(..., description="URL of the job listing")
    title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")
    metadata: Optional[JobListingMetadata] = Field(
        default=None, description="Additional job listing metadata including parsing"
    )
    status: str = Field(default="active", description="Status of the job listing")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class JobListingCreate(BaseModel):
    """Model for creating a new job listing"""

    url: str = Field(..., min_length=1, description="URL of the job listing")
    title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")


class JobListingUpdate(BaseModel):
    """Model for updating a job listing"""

    url: Optional[str] = Field(
        default=None, min_length=1, description="URL of the job listing"
    )
    title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")
    metadata: Optional[JobListingMetadata] = Field(
        default=None, description="Job listing metadata"
    )
    status: Optional[str] = Field(default=None, description="Status of the job listing")


class JobListingResponse(BaseModel):
    """Model for job listing response"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[JobListingMetadata] = None
    status: str
    created_at: datetime
    updated_at: datetime
