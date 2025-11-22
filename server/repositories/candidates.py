"""
Repository for candidate operations
"""

import base64
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from models.candidates import (
    CandidateModel,
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateMetadata,
)
from models.candidate_files import CandidateFileCreate
from database import get_collection
from integrations.agents.cv_parser_agent import (
    run_agent_cv_categorization,
    run_workflow,
    WorkflowInput,
)


class CandidateRepository:
    """Repository for candidate CRUD operations"""

    def __init__(self):
        self.collection: Collection = get_collection("candidates")

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
            print(f"Retrieved candidate: {candidate}")
            if candidate:
                candidate["_id"] = str(candidate["_id"])
                return CandidateResponse(**candidate)
            return None
        except Exception as e:
            print(f"Error getting candidate: {e}")
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
            from repositories.candidate_files import candidate_file_repository

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
            # workflow_input = WorkflowInput(input_as_text=cv_file_path)
            # result = await run_workflow(workflow_input)

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


# Global repository instance
candidate_repository = CandidateRepository()
