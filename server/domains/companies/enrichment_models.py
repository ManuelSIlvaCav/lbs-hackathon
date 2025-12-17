"""
Models for enriched company data from Apollo.io
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class CompanyEnrichmentData(BaseModel):
    """Saved enrichment data in MongoDB"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    company_id: str  # Reference to company
    provider: str = "apollo"  # Provider name
    raw_data: Dict[str, Any]  # Full Apollo response
    enriched_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CompanyEnrichmentCreate(BaseModel):
    """Model for creating enrichment record"""

    company_id: str
    provider: str = "apollo"
    raw_data: Dict[str, Any]


class CompanyEnrichmentResponse(BaseModel):
    """Response model for enrichment data"""

    id: str
    company_id: str
    provider: str
    enriched_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CompanyJobEnrichmentData(BaseModel):
    """Saved job listings enrichment data in MongoDB"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    company_id: str  # Reference to company
    provider: str = "apollo"  # Provider name
    raw_data: Dict[str, Any]  # Full job listings response
    job_count: int = 0  # Number of jobs found
    enriched_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CompanyJobEnrichmentCreate(BaseModel):
    """Model for creating job enrichment record"""

    company_id: str
    provider: str = "apollo"
    raw_data: Dict[str, Any]
    job_count: int = 0


class CompanyJobEnrichmentResponse(BaseModel):
    """Response model for job enrichment data"""

    id: str
    company_id: str
    provider: str
    job_count: int
    enriched_at: Optional[datetime] = Field(
        default=None, description="When the job was last enriched"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
