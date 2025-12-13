"""
Repository for candidate and candidate file operations
"""

import base64
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from pymongo import ASCENDING

from .models import (
    CandidateModel,
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateMetadata,
    CandidateFileModel,
    CandidateFileCreate,
    CandidateFileUpdate,
    CandidateFileResponse,
    CandidateFileWithDataResponse,
)
from database import get_collection
from integrations.agents.cv_parser_agent import (
    run_agent_cv_categorization,
)

import logging

logger = logging.getLogger("app")

# ============================================================================
# Candidate Repository
# ============================================================================


class CandidateRepository:
    """Repository for candidate CRUD operations"""

    def __init__(self):
        self.collection: Collection = get_collection("candidates")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Create index on user_id for fast lookups
            self.collection.create_index(
                [("user_id", ASCENDING)],
                name="user_id_index",
                background=True,
                unique=True,  # Each user should have only one candidate profile
            )
            # Create index on followed_companies.company_id for fast lookups
            self.collection.create_index(
                [("followed_companies.company_id", ASCENDING)],
                name="followed_companies_company_id_index",
                background=True,
            )
            print("✓ Candidate indexes created successfully")
        except Exception as e:
            print(f"Note: Index creation handled by MongoDB: {e}")

    def create_candidate(self, candidate_data: CandidateCreate) -> CandidateResponse:
        """
        Create a new candidate in the database

        Args:
            candidate_data: CandidateCreate object with candidate information

        Returns:
            CandidateResponse object with created candidate data including ID
        """
        # Create candidate model with timestamps
        candidate = CandidateModel(
            user_id=candidate_data.user_id,
            name=candidate_data.name,
            email=candidate_data.email,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion (exclude id field)
        candidate_dict = candidate.model_dump(by_alias=True, exclude=["id"])

        # Insert into database
        result: InsertOneResult = self.collection.insert_one(candidate_dict)

        # Retrieve the inserted document
        inserted_candidate = self.collection.find_one({"_id": result.inserted_id})

        if not inserted_candidate:
            raise ValueError("Failed to retrieve inserted candidate")

        # Convert ObjectId to string for response
        inserted_candidate["_id"] = str(inserted_candidate["_id"])

        return CandidateResponse(**inserted_candidate)

    def get_candidate_by_user_id(self, user_id: str) -> Optional[CandidateResponse]:
        """
        Get a candidate by user_id

        Args:
            user_id: String representation of user's MongoDB ObjectId

        Returns:
            CandidateResponse if found, None otherwise
        """
        try:
            candidate = self.collection.find_one({"user_id": user_id})
            if candidate:
                candidate["_id"] = str(candidate["_id"])
                return CandidateResponse(**candidate)
            return None
        except Exception as e:
            print(f"Error getting candidate by user_id: {e}")
            return None

    def get_candidate_by_id(self, candidate_id: str) -> Optional[CandidateResponse]:
        """
        Get a candidate by ID

        Args:
            candidate_id: String representation of MongoDB ObjectId

        Returns:
            CandidateResponse if found, None otherwise
        """
        try:
            candidate = self.collection.find_one({"_id": ObjectId(candidate_id)})
            if candidate:
                candidate["_id"] = str(candidate["_id"])
                return CandidateResponse(**candidate)
            return None
        except Exception as e:
            print(f"Error getting candidate: {e}")
            logger.error(f"Error getting candidate", extra={"error_msg": e})
            return None

    def get_all_candidates(
        self, skip: int = 0, limit: int = 100
    ) -> List[CandidateResponse]:
        """
        Get all candidates with pagination

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List of CandidateResponse objects
        """
        candidates = []
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)

        for candidate in cursor:
            candidate["_id"] = str(candidate["_id"])
            candidates.append(CandidateResponse(**candidate))

        return candidates

    def update_candidate(
        self, candidate_id: str, candidate_data: CandidateUpdate
    ) -> Optional[CandidateResponse]:
        """
        Update a candidate

        Args:
            candidate_id: String representation of MongoDB ObjectId
            candidate_data: CandidateUpdate object with updated data (all fields optional)

        Returns:
            Updated CandidateResponse if successful, None otherwise
        """
        try:
            # Only include fields that were actually set (not None)
            update_data = candidate_data.model_dump(
                exclude_unset=True, exclude_none=True
            )

            # If there's nothing to update, return the current candidate
            if not update_data:
                return self.get_candidate_by_id(candidate_id)

            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.now()

            print(f"Updating candidate {candidate_id} with data: {update_data}")

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(candidate_id)}, {"$set": update_data}
            )

            print(f"Update result: {result} {result.modified_count}")

            if result.modified_count > 0:
                return self.get_candidate_by_id(candidate_id)
            return None
        except Exception as e:
            print(f"Error updating candidate: {e}")
            return None

    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete a candidate

        Args:
            candidate_id: String representation of MongoDB ObjectId

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            result: DeleteResult = self.collection.delete_one(
                {"_id": ObjectId(candidate_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting candidate: {e}")
            return False

    def get_candidate_count(self) -> int:
        """
        Get total count of candidates

        Returns:
            Total number of candidates in the collection
        """
        return self.collection.count_documents({})

    async def parse_cv(
        self, candidate_id: str, cv_file_path: str
    ) -> Optional[CandidateResponse]:
        """
        Parse a CV file using the CV parser agent, save the file to database,
        and update the candidate with parsed results

        Args:
            candidate_id: String representation of MongoDB ObjectId
            cv_file_path: Path to the CV file to parse

        Returns:
            Updated CandidateResponse with parsed CV data, None if failed
        """
        try:
            # Check if candidate exists
            candidate = self.get_candidate_by_id(candidate_id)
            if not candidate:
                print(f"Candidate {candidate_id} not found")
                return None

            # Read and encode the file to base64
            file_data_base64 = await self._encode_file_to_base64(cv_file_path)
            if not file_data_base64:
                print("Failed to encode CV file")
                return None

            # Get file metadata
            file_name = os.path.basename(cv_file_path)
            file_size = os.path.getsize(cv_file_path)

            # Save file to candidate_files collection
            file_create = CandidateFileCreate(
                candidate_id=candidate_id,
                file_name=file_name,
                file_type="application/pdf",
                file_size=file_size,
                file_data_base64=file_data_base64,
                file_category="cv",
            )

            saved_file = candidate_file_repository.create_file(file_create)
            print(f"Saved CV file with ID: {saved_file.id}")

            # Run the CV parser agent
            parsed_data = await self._run_cv_parser(cv_file_path)

            if not parsed_data:
                print("Failed to parse CV")
                return None

            # Create metadata with the categorization schema
            metadata = CandidateMetadata(categorization_schema=parsed_data)

            # Update the candidate with the parsed data
            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(candidate_id)},
                {
                    "$set": {
                        "name": metadata.categorization_schema.contact_info.full_name,
                        "email": metadata.categorization_schema.contact_info.email,
                        "metadata": metadata.model_dump(),
                        "updated_at": datetime.now(),
                    }
                },
            )

            if result.modified_count > 0:
                return self.get_candidate_by_id(candidate_id)
            return None

        except Exception as e:
            print(f"Error parsing CV: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def _encode_file_to_base64(self, file_path: str) -> Optional[str]:
        """
        Helper method to encode a file to base64

        Args:
            file_path: Path to the file to encode

        Returns:
            Base64 encoded string, None if failed
        """
        try:
            with open(file_path, "rb") as file:
                file_bytes = file.read()
                encoded = base64.b64encode(file_bytes).decode("utf-8")
                return encoded
        except Exception as e:
            print(f"Error encoding file to base64: {e}")
            return None

    async def _run_cv_parser(self, cv_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Helper method to run the CV parser workflow

        Args:
            cv_file_path: Path to the CV file

        Returns:
            Parsed CV data as dictionary, None if failed
        """
        try:
            result = await run_agent_cv_categorization(cv_file_path)

            print(f"CV parser result: {result}")

            if result and "output_parsed" in result:
                return result["output_parsed"]

            if result and isinstance(result, dict):
                return result

            return result

        except Exception as e:
            print(f"Error running CV parser: {e}")
            return None

    def follow_company(
        self, candidate_id: str, company_id: str
    ) -> Optional[CandidateResponse]:
        """
        Add a company to the candidate's followed companies list

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId
            company_id: String representation of company's MongoDB ObjectId

        Returns:
            Updated CandidateResponse if successful, None otherwise
        """
        try:
            from .models import FollowedCompany

            # Convert company_id to ObjectId
            company_oid = (
                ObjectId(company_id) if isinstance(company_id, str) else company_id
            )

            print(
                f"Following company - candidate_id: {candidate_id}, company_id: {company_id}, company_oid: {company_oid}"
            )

            # Check if already following
            existing = self.collection.find_one(
                {
                    "_id": ObjectId(candidate_id),
                    "followed_companies.company_id": company_oid,
                }
            )

            if existing:
                # Already following, return current state
                print("Already following this company")
                return self.get_candidate_by_id(candidate_id)

            # Add to followed companies
            # Store company_id as ObjectId directly, not as string
            followed_company_doc = {
                "company_id": company_oid,  # Store as ObjectId
                "followed_at": datetime.now(),
            }

            print(f"Following company dict to be pushed: {followed_company_doc}")

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(candidate_id)},
                {
                    "$push": {"followed_companies": followed_company_doc},
                    "$set": {"updated_at": datetime.now()},
                },
            )

            print(
                f"Follow result - matched: {result.matched_count}, modified: {result.modified_count}"
            )

            if result.modified_count > 0:
                return self.get_candidate_by_id(candidate_id)

            return None

        except Exception as e:
            print(f"Error following company: {e}")
            return None

    def unfollow_company(
        self, candidate_id: str, company_id: str
    ) -> Optional[CandidateResponse]:
        """
        Remove a company from the candidate's followed companies list

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId
            company_id: String representation of company's MongoDB ObjectId

        Returns:
            Updated CandidateResponse if successful, None otherwise
        """
        try:
            # Convert company_id to ObjectId
            company_oid = (
                ObjectId(company_id) if isinstance(company_id, str) else company_id
            )

            print(
                f"Unfollowing company - candidate_id: {candidate_id}, company_id: {company_id}, company_oid: {company_oid}"
            )

            # Check current state before unfollowing
            candidate_before = self.collection.find_one({"_id": ObjectId(candidate_id)})
            if candidate_before:
                print(
                    f"Candidate before unfollow: {candidate_before.get('followed_companies', [])}"
                )

            # Remove from followed companies
            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(candidate_id)},
                {
                    "$pull": {"followed_companies": {"company_id": company_oid}},
                    "$set": {"updated_at": datetime.now()},
                },
            )

            print(
                f"Unfollow result - matched: {result.matched_count}, modified: {result.modified_count}"
            )

            if result.modified_count > 0:
                return self.get_candidate_by_id(candidate_id)

            # Even if not modified (wasn't following), return current state
            return self.get_candidate_by_id(candidate_id)

        except Exception as e:
            print(f"Error unfollowing company: {e}")
            import traceback

            traceback.print_exc()
            return None


# ============================================================================
# Candidate File Repository
# ============================================================================


class CandidateFileRepository:
    """Repository for candidate file CRUD operations"""

    def __init__(self):
        self.collection: Collection = get_collection("candidate_files")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Create index on candidate_id for fast lookups
            self.collection.create_index(
                [("candidate_id", ASCENDING)],
                name="candidate_id_index",
                background=True,
            )
            print("✓ Candidate files indexes created successfully")
        except Exception as e:
            print(f"Note: Index creation handled by MongoDB: {e}")

    def create_file(
        self, file_data: CandidateFileCreate
    ) -> CandidateFileWithDataResponse:
        """
        Create a new candidate file record in the database

        Args:
            file_data: CandidateFileCreate object with file information and base64 data

        Returns:
            CandidateFileWithDataResponse object with created file data including ID
        """
        # Create file model with timestamps
        file_model = CandidateFileModel(
            candidate_id=file_data.candidate_id,
            file_name=file_data.file_name,
            file_type=file_data.file_type,
            file_size=file_data.file_size,
            file_data_base64=file_data.file_data_base64,
            file_category=file_data.file_category,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion (exclude id field)
        file_dict = file_model.model_dump(by_alias=True, exclude=["id"])

        # Insert into database
        result: InsertOneResult = self.collection.insert_one(file_dict)

        # Retrieve the inserted document
        inserted_file = self.collection.find_one({"_id": result.inserted_id})

        if not inserted_file:
            raise ValueError("Failed to retrieve inserted candidate file")

        # Convert ObjectId to string for response
        inserted_file["_id"] = str(inserted_file["_id"])

        return CandidateFileWithDataResponse(**inserted_file)

    def get_file_by_id(
        self, file_id: str, include_data: bool = False
    ) -> Optional[CandidateFileWithDataResponse | CandidateFileResponse]:
        """
        Get a candidate file by ID

        Args:
            file_id: String representation of MongoDB ObjectId
            include_data: Whether to include base64 file data in response

        Returns:
            CandidateFileWithDataResponse or CandidateFileResponse if found, None otherwise
        """
        try:
            if include_data:
                file_doc = self.collection.find_one({"_id": ObjectId(file_id)})
                if file_doc:
                    file_doc["_id"] = str(file_doc["_id"])
                    return CandidateFileWithDataResponse(**file_doc)
            else:
                # Exclude base64 data for listing
                file_doc = self.collection.find_one(
                    {"_id": ObjectId(file_id)}, {"file_data_base64": 0}
                )
                if file_doc:
                    file_doc["_id"] = str(file_doc["_id"])
                    return CandidateFileResponse(**file_doc)
            return None
        except Exception as e:
            print(f"Error getting candidate file: {e}")
            return None

    def get_files_by_candidate(
        self, candidate_id: str, file_category: Optional[str] = None
    ) -> List[CandidateFileResponse]:
        """
        Get all files for a specific candidate

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId
            file_category: Optional filter by file category (cv, cover_letter, etc.)

        Returns:
            List of CandidateFileResponse objects (without base64 data)
        """
        query = {"candidate_id": candidate_id}
        if file_category:
            query["file_category"] = file_category

        files = []
        # Exclude base64 data for listing performance
        cursor = self.collection.find(query, {"file_data_base64": 0}).sort(
            "created_at", -1
        )

        for file_doc in cursor:
            file_doc["_id"] = str(file_doc["_id"])
            files.append(CandidateFileResponse(**file_doc))

        return files

    def get_latest_cv_for_candidate(
        self, candidate_id: str
    ) -> Optional[CandidateFileWithDataResponse]:
        """
        Get the most recent CV file for a candidate

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId

        Returns:
            CandidateFileWithDataResponse with base64 data if found, None otherwise
        """
        try:
            file_doc = self.collection.find_one(
                {"candidate_id": candidate_id, "file_category": "cv"},
                sort=[("created_at", -1)],
            )
            if file_doc:
                file_doc["_id"] = str(file_doc["_id"])
                return CandidateFileWithDataResponse(**file_doc)
            return None
        except Exception as e:
            print(f"Error getting latest CV: {e}")
            return None

    def update_file(
        self, file_id: str, file_data: CandidateFileUpdate
    ) -> Optional[CandidateFileResponse]:
        """
        Update a candidate file's metadata (not the actual file content)

        Args:
            file_id: String representation of MongoDB ObjectId
            file_data: CandidateFileUpdate object with updated metadata

        Returns:
            Updated CandidateFileResponse if successful, None otherwise
        """
        try:
            # Only include fields that were actually set (not None)
            update_data = file_data.model_dump(exclude_unset=True, exclude_none=True)

            # If there's nothing to update, return the current file
            if not update_data:
                return self.get_file_by_id(file_id, include_data=False)

            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.now()

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(file_id)}, {"$set": update_data}
            )

            if result.modified_count > 0:
                return self.get_file_by_id(file_id, include_data=False)
            return None
        except Exception as e:
            print(f"Error updating candidate file: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a candidate file

        Args:
            file_id: String representation of MongoDB ObjectId

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            result: DeleteResult = self.collection.delete_one(
                {"_id": ObjectId(file_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting candidate file: {e}")
            return False

    def delete_files_by_candidate(self, candidate_id: str) -> int:
        """
        Delete all files for a specific candidate

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId

        Returns:
            Number of files deleted
        """
        try:
            result: DeleteResult = self.collection.delete_many(
                {"candidate_id": candidate_id}
            )
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting candidate files: {e}")
            return 0

    def get_file_count_by_candidate(self, candidate_id: str) -> int:
        """
        Get total count of files for a specific candidate

        Args:
            candidate_id: String representation of candidate's MongoDB ObjectId

        Returns:
            Total number of files for the candidate
        """
        return self.collection.count_documents({"candidate_id": candidate_id})


# Global repository instances
candidate_repository = CandidateRepository()
candidate_file_repository = CandidateFileRepository()
