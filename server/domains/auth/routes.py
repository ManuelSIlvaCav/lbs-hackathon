"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional

from .models import UserCreate, UserLogin, Token, UserResponse, UserRole, UserInDB
from .repository import user_repository
from .utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)

# Import candidate repository to create profiles
from domains.candidates.repository import candidate_repository
from domains.candidates.models import CandidateCreate

import logging

logger = logging.getLogger("app")

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user by email and password

    Args:
        email: User email
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user = user_repository.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get current authenticated user

    Args:
        token: JWT token from Authorization header

    Returns:
        Current user

    Raises:
        HTTPException if authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(token, credentials_exception)

    user = user_repository.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """
    Dependency to get current active user

    Args:
        current_user: Current user from token

    Returns:
        Current active user

    Raises:
        HTTPException if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Dependency to require admin role

    Args:
        current_user: Current active user

    Returns:
        Current admin user

    Raises:
        HTTPException if user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_create: UserCreate):
    """
    Register a new user

    Args:
        user_create: User registration data

    Returns:
        JWT token and user data

    Raises:
        HTTPException if email already exists
    """
    try:
        # Create user
        user = user_repository.create_user(user_create)

        # Create candidate profile for the new user
        candidate_data = CandidateCreate(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
        )
        candidate = candidate_repository.create_candidate(candidate_data)

        # Link candidate_id to user
        user_repository.update_candidate_id(user.id, candidate.id)

        # Update user object with candidate_id
        user.candidate_id = candidate.id

        # Create access token with candidate_id
        access_token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role.value,
                "candidate_id": candidate.id,
            }
        )

        # Create refresh token
        refresh_token = create_refresh_token(
            data={
                "sub": user.email,
                "role": user.role.value,
                "candidate_id": candidate.id,
            }
        )

        # Return token and user
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                candidate_id=candidate.id,
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """
    Login for regular users

    Args:
        user_login: Login credentials

    Returns:
        JWT token and user data

    Raises:
        HTTPException if credentials are invalid
    """
    user = authenticate_user(user_login.email, user_login.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Check if user has a candidate profile, create if not
    candidate = candidate_repository.get_candidate_by_user_id(user.id)

    if not candidate:
        # Create candidate profile for existing user
        candidate_data = CandidateCreate(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
        )
        candidate = candidate_repository.create_candidate(candidate_data)

        # Link candidate_id to user
        user_repository.update_candidate_id(user.id, candidate.id)

        # Update user object with candidate_id
        user.candidate_id = candidate.id
    else:
        # If candidate exists but user.candidate_id is not set, update it
        if not user.candidate_id:
            user_repository.update_candidate_id(user.id, candidate.id)
            user.candidate_id = candidate.id

    # Create access token with candidate_id
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": candidate.id,
        }
    )

    # Create refresh token
    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": candidate.id,
        }
    )

    # Return token and user
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            candidate_id=candidate.id,
        ),
    )


@router.post("/admin/login", response_model=Token)
async def admin_login(user_login: UserLogin):
    """
    Login for admin users only

    Args:
        user_login: Login credentials

    Returns:
        JWT token and user data

    Raises:
        HTTPException if credentials are invalid or user is not admin
    """
    user = authenticate_user(user_login.email, user_login.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Check admin role
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin access required.",
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": user.candidate_id,
        }
    )

    # Create refresh token
    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": user.candidate_id,
        }
    )

    # Return token and user
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            candidate_id=user.candidate_id,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        candidate_id=current_user.candidate_id,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token: str):
    """
    Refresh access token using a valid refresh token

    Args:
        token: Refresh token

    Returns:
        New access token and refresh token

    Raises:
        HTTPException if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the refresh token
    token_data = verify_token(token, credentials_exception)

    # Get user from database
    user = user_repository.get_user_by_email(email=token_data.email)
    if user is None or not user.is_active:
        raise credentials_exception

    # Create new access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": user.candidate_id,
        }
    )

    # Create new refresh token
    new_refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "candidate_id": user.candidate_id,
        }
    )

    # Return new tokens
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            candidate_id=user.candidate_id,
        ),
    )


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Logout user (client should discard tokens)

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # In a stateless JWT system, logout is handled client-side by discarding tokens
    # For added security, you could implement token blacklisting here
    return {"message": "Successfully logged out"}
