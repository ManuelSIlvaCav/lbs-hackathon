"""
User and authentication models
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles"""

    USER = "user"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """User model as stored in database"""

    id: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: Optional[str] = None


class UserResponse(BaseModel):
    """User response model (without password)"""

    id: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Data stored in JWT token"""

    email: Optional[str] = None
    role: Optional[str] = None
