"""
Models for search options data
"""

from typing import Annotated, Optional, List
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class SearchOptionsModel(BaseModel):
    """Model for search options data"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    countries: List[str] = Field(default_factory=list, description="List of countries")
    profile_categories: List[str] = Field(
        default_factory=list, description="List of profile categories"
    )
    role_titles: List[str] = Field(
        default_factory=list, description="List of role titles"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SearchOptionsResponse(BaseModel):
    """Model for search options response"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
    )

    countries: List[str]
    profile_categories: List[str]
    role_titles: List[str]
    updated_at: datetime
