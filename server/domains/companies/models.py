"""
Company models
"""

from datetime import datetime
from typing import Optional
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


class CompanyModel(BaseModel):
    """Company database model"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    company_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CompanyResponse(BaseModel):
    """Company response model"""

    id: str
    name: str
    company_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CompanyCreate(BaseModel):
    """Model for creating a company"""

    name: str
    company_url: str  # Required now

    @property
    def is_valid_url(self) -> bool:
        """Check if company_url is a valid URL"""
        if not self.company_url:
            return False
        return self.company_url.startswith(("http://", "https://"))


class CompanySearchParams(BaseModel):
    """Parameters for company search"""

    query: str = ""
    skip: int = 0
    limit: int = 20
