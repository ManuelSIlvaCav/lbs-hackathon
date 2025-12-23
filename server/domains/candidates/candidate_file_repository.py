import base64
import os
import tempfile
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from pymongo import ASCENDING

from utils.singleton_class import SingletonMeta

from .models import (
    CandidateFileModel,
    CandidateFileCreate,
    CandidateFileUpdate,
    CandidateFileResponse,
    CandidateFileWithDataResponse,
)
from database import get_collection

import logging

logger = logging.getLogger("app")

# ============================================================================
# Candidate File Repository
# ============================================================================


class CandidateFileRepository(metaclass=SingletonMeta):
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

    def get_candidate_cv_file(self, candidate_id: str):
        # Load the latest CV file from candidate_files collection
        latest_cv = candidate_file_repository.get_latest_cv_for_candidate(candidate_id)
        if not latest_cv:
            raise ValueError(f"No CV file found for candidate {candidate_id}")

        # Decode base64 CV data to bytes
        cv_bytes = base64.b64decode(latest_cv.file_data_base64)

        # Create a temporary file to store the PDF
        # Use suffix from original filename to preserve extension
        file_extension = os.path.splitext(latest_cv.file_name)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension, mode="wb"
        ) as temp_file:
            temp_file.write(cv_bytes)
            cv_file_path = temp_file.name

        print(f"Created temporary CV file at: {cv_file_path}")
        return cv_file_path


candidate_file_repository = CandidateFileRepository()
