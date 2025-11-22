"""
Models for candidate file storage
"""

from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


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
