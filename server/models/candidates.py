from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId

from integrations.agents.cv_parser_agent import AgentCvCategorizationSchema


# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


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
    name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Candidate's email address")
    metadata: Optional[CandidateMetadata] = Field(
        default=None, description="Additional candidate metadata including CV parsing"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CandidateCreate(BaseModel):
    """Model for creating a new candidate"""

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


class CandidateResponse(BaseModel):
    """Model for candidate response"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    name: str = None
    email: Optional[str] = None
    metadata: Optional[CandidateMetadata] = None
    created_at: datetime
    updated_at: datetime
