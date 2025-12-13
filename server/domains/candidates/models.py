"""
Models for candidates and candidate files
"""

from typing import Annotated, List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict, field_validator
from bson import ObjectId

from integrations.agents.cv_parser_agent import AgentCvCategorizationSchema


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


# ============================================================================
# Followed Company Model
# ============================================================================


class FollowedCompany(BaseModel):
    """Model for a company followed by a candidate"""

    company_id: PyObjectId = Field(
        ..., description="Reference to company (MongoDB ObjectId)"
    )
    followed_at: datetime = Field(
        default_factory=datetime.now, description="When the company was followed"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )


# ============================================================================
# Search Preferences Models
# ============================================================================


class SearchPreferences(BaseModel):
    """Search preferences for job matching"""

    # Location preferences
    locations: Optional[List[str]] = Field(
        default=None,
        description="Preferred work locations (e.g., 'Remote', 'London', 'New York')",
    )
    visa_sponsorship: Optional[Dict[str, bool]] = Field(
        default=None, description="Visa sponsorship requirements by region (uk, eu, us)"
    )
    languages: Optional[List[str]] = Field(default=None, description="Languages spoken")

    @field_validator("visa_sponsorship", mode="before")
    @classmethod
    def convert_visa_sponsorship(cls, v):
        """Convert legacy boolean visa_sponsorship to dict format"""
        if v is None:
            return None
        if isinstance(v, bool):
            # Convert old boolean format to new dict format
            # If True, enable all regions; if False, disable all regions
            return {"uk": v, "eu": v, "us": v}
        if isinstance(v, dict):
            # Ensure all required keys exist
            result = {"uk": False, "eu": False, "us": False}
            result.update(v)
            return result
        return v

    # Role preferences
    role_type: Optional[List[str]] = Field(
        default=None,
        description="Type of roles (e.g., 'Full-time', 'Contract', 'Internship')",
    )
    role_level: Optional[List[str]] = Field(
        default=None,
        description="Level of roles (e.g., 'Junior', 'Mid', 'Senior', 'Lead')",
    )
    minimum_salary: Optional[int] = Field(
        default=None, description="Minimum salary requirement"
    )
    role_priorities: Optional[List[str]] = Field(
        default=None,
        description="Priority aspects (e.g., 'Work-life balance', 'Learning', 'Impact')",
    )

    # Industry and technology preferences
    favourite_industries: Optional[List[str]] = Field(
        default=None, description="Preferred industries"
    )
    hidden_industries: Optional[List[str]] = Field(
        default=None, description="Industries to avoid"
    )
    favourite_technologies: Optional[List[str]] = Field(
        default=None, description="Preferred technologies/skills"
    )
    hidden_technologies: Optional[List[str]] = Field(
        default=None, description="Technologies to avoid"
    )

    # Company preferences
    company_size: Optional[List[str]] = Field(
        default=None,
        description="Preferred company sizes (e.g., 'Startup', 'Scale-up', 'Enterprise')",
    )
    hidden_companies: Optional[List[str]] = Field(
        default=None, description="List of company IDs to hide"
    )


# ============================================================================
# Candidate Models
# ============================================================================


class CandidateMetadata(BaseModel):
    """Metadata for candidate including CV parsing results"""

    categorization_schema: Optional[AgentCvCategorizationSchema] = Field(
        default=None, description="Parsed CV data from AgentCvCategorizationSchema"
    )


class CandidateModel(BaseModel):
    """Model for candidate data"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str = Field(
        ..., description="Reference to user account (MongoDB ObjectId as string)"
    )
    name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Candidate's email address")
    metadata: Optional[CandidateMetadata] = Field(
        default=None, description="Additional candidate metadata including CV parsing"
    )
    search_preferences: Optional[SearchPreferences] = Field(
        default=None, description="Job search preferences and filters"
    )
    followed_companies: Optional[List[FollowedCompany]] = Field(
        default=None, description="List of companies followed by the candidate"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CandidateCreate(BaseModel):
    """Model for creating a new candidate"""

    user_id: str = Field(..., description="Reference to user account")
    name: str = Field(..., min_length=1, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Candidate's email address")


class CandidateUpdate(BaseModel):
    """Model for updating a candidate"""

    name: Optional[str] = Field(
        default=None, min_length=1, description="Candidate's full name"
    )
    email: Optional[str] = Field(default=None, description="Candidate's email address")
    metadata: Optional[CandidateMetadata] = Field(
        default=None, description="Candidate metadata"
    )
    search_preferences: Optional[SearchPreferences] = Field(
        default=None, description="Job search preferences"
    )


class CandidateResponse(BaseModel):
    """Model for candidate response"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    user_id: str
    name: str = None
    email: Optional[str] = None
    metadata: Optional[CandidateMetadata] = None
    search_preferences: Optional[SearchPreferences] = None
    followed_companies: Optional[List[FollowedCompany]] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Candidate File Models
# ============================================================================


class CandidateFileModel(BaseModel):
    """Model for candidate file data stored in MongoDB"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    candidate_id: str = Field(
        ..., description="Reference to the candidate (MongoDB ObjectId as string)"
    )
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(
        default="application/pdf", description="MIME type of the file"
    )
    file_size: int = Field(..., description="File size in bytes")
    file_data_base64: str = Field(..., description="Base64 encoded file content (PDF)")
    file_category: str = Field(
        default="cv",
        description="Category of file: cv, cover_letter, certificate, etc.",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CandidateFileCreate(BaseModel):
    """Model for creating a new candidate file"""

    candidate_id: str = Field(..., description="Reference to the candidate")
    file_name: str = Field(..., min_length=1, description="Original file name")
    file_type: str = Field(
        default="application/pdf", description="MIME type of the file"
    )
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_data_base64: str = Field(
        ..., min_length=1, description="Base64 encoded file content"
    )
    file_category: str = Field(
        default="cv",
        description="Category of file: cv, cover_letter, certificate, etc.",
    )


class CandidateFileUpdate(BaseModel):
    """Model for updating a candidate file (mainly metadata)"""

    file_name: Optional[str] = Field(
        default=None, min_length=1, description="Original file name"
    )
    file_category: Optional[str] = Field(default=None, description="Category of file")


class CandidateFileResponse(BaseModel):
    """Model for candidate file response (without base64 data for listing)"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    candidate_id: str
    file_name: str
    file_type: str
    file_size: int
    file_category: str
    created_at: datetime
    updated_at: datetime


class CandidateFileWithDataResponse(BaseModel):
    """Model for candidate file response with base64 data (for download)"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    candidate_id: str
    file_name: str
    file_type: str
    file_size: int
    file_data_base64: str
    file_category: str
    created_at: datetime
    updated_at: datetime
