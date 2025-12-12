"""
User repository for database operations
"""

from typing import Optional
from datetime import datetime
from bson import ObjectId

from database import get_collection
from pymongo.collection import Collection

from .models import UserCreate, UserInDB, UserRole
from .utils import get_password_hash

import logging

logger = logging.getLogger("app")


class UserRepository:
    def __init__(self):
        """Initialize repository with database client"""
        self.collection: Collection = get_collection("users")

        # Create unique index on email
        self.collection.create_index("email", unique=True)
        logger.info("UserRepository initialized")

    def create_user(self, user_create: UserCreate) -> UserInDB:
        """
        Create a new user

        Args:
            user_create: User creation data

        Returns:
            Created user

        Raises:
            ValueError if email already exists
        """
        # Check if user exists
        existing_user = self.collection.find_one({"email": user_create.email})
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = get_password_hash(user_create.password)

        # Create user document
        user_dict = {
            "email": user_create.email,
            "hashed_password": hashed_password,
            "full_name": user_create.full_name,
            "role": user_create.role.value,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "candidate_id": None,  # Will be set when candidate profile is created
        }

        # Insert into database
        result = self.collection.insert_one(user_dict)

        # Return created user
        return UserInDB(
            id=str(result.inserted_id),
            email=user_dict["email"],
            hashed_password=user_dict["hashed_password"],
            full_name=user_dict.get("full_name"),
            role=UserRole(user_dict["role"]),
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            candidate_id=user_dict.get("candidate_id"),
        )

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        user_doc = self.collection.find_one({"email": email})

        if not user_doc:
            return None

        return UserInDB(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            hashed_password=user_doc["hashed_password"],
            full_name=user_doc.get("full_name"),
            role=UserRole(user_doc.get("role", "user")),
            is_active=user_doc.get("is_active", True),
            created_at=user_doc.get("created_at"),
            candidate_id=user_doc.get("candidate_id"),
        )

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        if not ObjectId.is_valid(user_id):
            return None

        user_doc = self.collection.find_one({"_id": ObjectId(user_id)})

        if not user_doc:
            return None

        return UserInDB(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            hashed_password=user_doc["hashed_password"],
            full_name=user_doc.get("full_name"),
            role=UserRole(user_doc.get("role", "user")),
            is_active=user_doc.get("is_active", True),
            created_at=user_doc.get("created_at"),
            candidate_id=user_doc.get("candidate_id"),
        )

    def update_candidate_id(self, user_id: str, candidate_id: str) -> bool:
        """
        Update user's candidate_id after candidate profile is created

        Args:
            user_id: User ID
            candidate_id: Candidate ID to link

        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"candidate_id": candidate_id}}
        )
        return result.modified_count > 0


# Singleton instance
user_repository = UserRepository()
