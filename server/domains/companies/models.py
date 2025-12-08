"""
Company models
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):

        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema(
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(cls.validate),
                    ]
                ),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        return {"type": "string"}


class CompanyModel(BaseModel):
    """Company database model"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    company_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = None
    industries: Optional[List[str]] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


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
