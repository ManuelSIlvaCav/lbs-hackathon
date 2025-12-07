"""
Models for company search providers (Apollo.io, etc.)
"""

from datetime import datetime
from typing import Optional, Dict, Any
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


class CompanySearchResult(BaseModel):
    """Saved company search result in MongoDB"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    provider: str  # "apollo", "theirstack", etc.
    search_query: str  # The query that found this company
    raw_data: Dict[str, Any]  # Full raw response from provider
    created_at: datetime = Field(default_factory=datetime.now)
    last_synced_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CompanySearchResultCreate(BaseModel):
    """Model for creating a company search result"""

    provider: str
    search_query: str
    raw_data: Dict[str, Any]


class CompanySearchResultResponse(BaseModel):
    """Response model for company search results"""

    id: str
    provider: str
    search_query: str
    created_at: datetime
    last_synced_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
