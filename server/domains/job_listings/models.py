"""
Models for job listing data
"""

from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId
from enum import Enum

from integrations.agents.job_listing_parser import AgentJobCategorizationSchema


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class CompanyInfo(BaseModel):
    """Embedded company information in job listing"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = Field(default=None, description="Company name")
    company_url: Optional[str] = Field(default=None, description="Company website URL")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn URL")
    logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    domain: Optional[str] = Field(default=None, description="Company domain")
    industries: Optional[list[str]] = Field(
        default=None, description="Company industries"
    )
    description: Optional[str] = Field(default=None, description="Company description")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )


class JobListingMetadata(BaseModel):
    """Metadata for job listing including parsed job description"""

    categorization_schema: Optional[AgentJobCategorizationSchema] = Field(
        default=None, description="Parsed job data from AgentJobCategorizationSchema"
    )
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class JobListingOrigin(str, Enum):
    LINKEDIN = "linkedin"
    CAREERS = "careers"
    GREENHOUSE = "greenhouse"


class JobListingStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CREATED = "created"


class JobListingSourceStatus(str, Enum):
    ENRICHED = "enriched"
    SCRAPPED = "scrapped"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"


class JobListingModel(BaseModel):
    """Model for job listing data - unified model for all job listings. Provider tracking moved to JobListingSourceModel."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
        use_enum_values=True,
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    url: str = Field(..., description="URL of the job listing")
    title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    company_id: Optional[PyObjectId] = Field(
        default=None, description="Reference to company document (ObjectId)"
    )
    location: Optional[str] = Field(default=None, description="Job location")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State")
    country: Optional[str] = Field(default=None, description="Country")
    description: Optional[str] = Field(default=None, description="Job description")
    posted_at: Optional[datetime] = Field(
        default=None, description="When the job was posted"
    )
    last_seen_at: Optional[datetime] = Field(
        default=None, description="When the job was last seen"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    origin: Optional[JobListingOrigin] = Field(
        default=None,
        description="Origin of the job listing data linkedin, careers, others",
    )
    origin_domain: Optional[str] = Field(
        default=None,
        description="Origin domain of the job listing URL",
    )
    profile_categories: Optional[list[str]] = Field(
        default=None, description="Profile categories assigned to the job listing"
    )
    role_titles: Optional[list[str]] = Field(
        default=None, description="Role titles assigned to the job listing"
    )
    employement_type: Optional[str] = Field(
        default=None, description="Type of employment (e.g., Full-time, Part-time)"
    )
    work_arrangement: Optional[str] = Field(
        default=None, description="Work arrangement (e.g., Remote, On-site, Hybrid)"
    )
    listing_status: Optional[JobListingStatus] = Field(
        default=JobListingStatus.CREATED,
        description="Status of the job listing (e.g., active, expired)",
    )
    source_status: Optional[JobListingSourceStatus] = Field(
        default=JobListingSourceStatus.SCRAPPED,
        description="Status of the job listing source (e.g., enriched, scrapped)",
    )
    salary_range_min: Optional[float] = Field(
        default=None, description="Minimum salary for the job listing"
    )
    salary_range_max: Optional[float] = Field(
        default=None, description="Maximum salary for the job listing"
    )
    salary_currency: Optional[str] = Field(
        default=None, description="Currency of the salary range (e.g., USD, EUR)"
    )
    deactivated_at: Optional[datetime] = Field(
        default=None,
        description="When the job listing was deactivated due to parsing failure",
    )
    company_info: Optional[CompanyInfo] = Field(
        default=None,
        description="Embedded company information from lookup (not stored in DB)",
    )


class JobListingCreate(BaseModel):
    """Model for creating a new job listing - provider tracking handled separately via JobListingSourceModel"""

    url: str = Field(..., min_length=1, description="URL of the job listing")
    title: str = Field(..., description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    company_id: Optional[PyObjectId] = Field(
        default=None, description="Reference to company document (ObjectId)"
    )
    location: Optional[str] = Field(default=None, description="Job location")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State")
    country: Optional[str] = Field(default=None, description="Country")
    description: Optional[str] = Field(default=None, description="Job description")
    posted_at: Optional[datetime] = Field(
        default=None, description="When the job was posted"
    )
    last_seen_at: Optional[datetime] = Field(
        default=None, description="When the job was last seen"
    )
    source_status: Optional[JobListingSourceStatus] = Field(
        default=JobListingSourceStatus.SCRAPPED,
        description="Status of the job listing source (e.g., enriched, scrapped)",
    )


class JobListingUpdate(BaseModel):
    """Model for updating a job listing"""

    url: Optional[str] = Field(
        default=None, min_length=1, description="URL of the job listing"
    )
    title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")


class PaginatedJobListingResponse(BaseModel):
    """Paginated response for job listings"""

    items: list[JobListingModel] = Field(
        default_factory=list, description="List of job listings"
    )
    total: int = Field(..., description="Total number of job listings matching filters")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more items to fetch")
