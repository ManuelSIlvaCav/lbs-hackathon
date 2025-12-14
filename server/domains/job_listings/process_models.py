"""
Models for job process tracking and locking
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Annotated
from pydantic import BeforeValidator

# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class JobProcessStatus:
    """Status constants for job processes"""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RELEASED = "released"


class JobProcessModel(BaseModel):
    """Model for tracking task/batch processing to prevent duplicates"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    task_name: str = Field(..., description="Name of the task/process being executed")
    task_instance_id: Optional[str] = Field(
        default=None, description="Celery task instance ID for tracking"
    )
    status: str = Field(
        default=JobProcessStatus.PROCESSING,
        description="Current status of the process",
    )
    started_at: datetime = Field(
        default_factory=datetime.now, description="When the process started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When the process completed"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if process failed"
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class JobProcessCreate(BaseModel):
    """Model for creating a task process lock"""

    task_name: str = Field(..., description="Name of the task/process being executed")
    task_instance_id: Optional[str] = Field(
        default=None, description="Celery task instance ID for tracking"
    )
