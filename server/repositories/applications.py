"""
Repository for application operations with joins
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult

from models.applications import (
    ApplicationModel,
    ApplicationCreate,
    ApplicationResponse,
    ApplicationWithDetailsResponse,
)
from models.candidates import CandidateResponse
from models.job_listings import JobListingResponse
from database import get_collection


class ApplicationRepository:
    """Repository for application CRUD operations with joins"""

    def __init__(self):
        self.collection: Collection = get_collection("applications")
        self.candidates_collection: Collection = get_collection("candidates")
        self.job_listings_collection: Collection = get_collection("job_listings")

    def _get_candidate_by_id(self, candidate_id: str) -> Optional[CandidateResponse]:
        """Helper method to get candidate data"""
        try:
            candidate = self.candidates_collection.find_one(
                {"_id": ObjectId(candidate_id)}
            )
            if candidate:
                candidate["_id"] = str(candidate["_id"])
                return CandidateResponse(**candidate)
        except Exception as e:
            print(f"Error getting candidate {candidate_id}: {e}")
        return None

    def _get_job_listing_by_id(
        self, job_listing_id: str
    ) -> Optional[JobListingResponse]:
        """Helper method to get job listing data"""
        try:
            job_listing = self.job_listings_collection.find_one(
                {"_id": ObjectId(job_listing_id)}
            )
            if job_listing:
                job_listing["_id"] = str(job_listing["_id"])
                return JobListingResponse(**job_listing)
        except Exception as e:
            print(f"Error getting job listing {job_listing_id}: {e}")
        return None

    def _enrich_application_with_details(
        self, application_dict: dict
    ) -> ApplicationWithDetailsResponse:
        """Enrich application with candidate and job listing details"""
        # Get candidate details
        candidate = self._get_candidate_by_id(application_dict["candidate_id"])

        # Handle backward compatibility: check for both old and new field names
        job_listing_id = application_dict.get("job_listing_id") or application_dict.get(
            "job_posting_id"
        )

        # Get job listing details
        job_listing = None
        if job_listing_id:
            job_listing = self._get_job_listing_by_id(job_listing_id)

        # Ensure the response always has job_listing_id field
        if (
            "job_listing_id" not in application_dict
            and "job_posting_id" in application_dict
        ):
            application_dict["job_listing_id"] = application_dict["job_posting_id"]

        # Create response with joined data
        return ApplicationWithDetailsResponse(
            **application_dict, candidate=candidate, job_listing=job_listing
        )

    def check_duplicate_application(
        self, candidate_id: str, job_listing_id: str, status: str
    ) -> bool:
        """
        Check if an application already exists for a candidate, job listing, and status

        Args:
            candidate_id: ID of the candidate
            job_listing_id: ID of the job listing
            status: Status of the application

        Returns:
            True if duplicate exists, False otherwise
        """
        # Check for both old and new field names for backward compatibility
        query = {
            "$or": [
                {
                    "candidate_id": candidate_id,
                    "job_listing_id": job_listing_id,
                    "status": status,
                },
                {
                    "candidate_id": candidate_id,
                    "job_posting_id": job_listing_id,
                    "status": status,
                },
            ]
        }
        existing = self.collection.find_one(query)
        return existing is not None

    def create_application(
        self, application_data: ApplicationCreate
    ) -> ApplicationWithDetailsResponse:
        """
        Create a new application in the database

        Args:
            application_data: ApplicationCreate object with application information

        Returns:
            ApplicationWithDetailsResponse object with created application data including joined details

        Raises:
            ValueError: If candidate or job listing not found, or if duplicate application exists
        """
        # Validate that candidate and job listing exist
        candidate = self._get_candidate_by_id(application_data.candidate_id)
        if not candidate:
            raise ValueError(
                f"Candidate with id {application_data.candidate_id} not found"
            )

        job_listing = self._get_job_listing_by_id(application_data.job_listing_id)
        if not job_listing:
            raise ValueError(
                f"Job listing with id {application_data.job_listing_id} not found"
            )

        # Check for duplicate application with same status
        if self.check_duplicate_application(
            application_data.candidate_id,
            application_data.job_listing_id,
            application_data.status,
        ):
            raise ValueError(
                f"Application already exists for candidate {application_data.candidate_id} "
                f"and job listing {application_data.job_listing_id} with status '{application_data.status}'"
            )

        # Create application model with timestamps
        application = ApplicationModel(
            job_listing_id=application_data.job_listing_id,
            candidate_id=application_data.candidate_id,
            accuracy_score=application_data.accuracy_score,
            status=application_data.status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion (exclude id field)
        application_dict = application.model_dump(by_alias=True, exclude=["id"])

        # Insert into database
        result: InsertOneResult = self.collection.insert_one(application_dict)

        # Retrieve the inserted document
        inserted_application = self.collection.find_one({"_id": result.inserted_id})

        if not inserted_application:
            raise ValueError("Failed to retrieve inserted application")

        # Convert ObjectId to string for response
        inserted_application["_id"] = str(inserted_application["_id"])

        # Return with joined details
        return self._enrich_application_with_details(inserted_application)

    def get_applications_by_candidate(
        self,
        candidate_id: str,
        skip: int = 0,
        limit: int = 100,
        include_details: bool = True,
    ) -> List[ApplicationWithDetailsResponse]:
        """
        Get all applications for a specific candidate

        Args:
            candidate_id: Candidate ID to filter by
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            include_details: Whether to include job listing details

        Returns:
            List of ApplicationWithDetailsResponse objects
        """
        query = {"candidate_id": candidate_id}

        applications = []
        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        )

        for application in cursor:
            application["_id"] = str(application["_id"])

            if include_details:
                applications.append(self._enrich_application_with_details(application))
            else:
                applications.append(ApplicationResponse(**application))

        return applications

    def get_applied_job_listing_ids(self, candidate_id: str) -> set:
        """
        Get all job listing IDs that a candidate has already applied to

        Args:
            candidate_id: ID of the candidate

        Returns:
            Set of job listing IDs (strings)
        """
        query = {"candidate_id": candidate_id}
        # Only fetch the job_listing_id field for efficiency
        cursor = self.collection.find(
            query,
            {
                "job_listing_id": 1,
            },
        )

        job_listing_ids = set()
        for application in cursor:
            # Handle both old and new field names
            if "job_listing_id" in application:
                job_listing_ids.add(application["job_listing_id"])
            elif "job_posting_id" in application:
                job_listing_ids.add(application["job_posting_id"])

        return job_listing_ids

    def update_application_status(
        self, application_id: str, status: str
    ) -> Optional[ApplicationWithDetailsResponse]:
        """
        Update application status

        Args:
            application_id: String representation of MongoDB ObjectId
            status: New status value

        Returns:
            Updated ApplicationWithDetailsResponse if successful, None otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"status": status, "updated_at": datetime.now()}},
            )

            if result.matched_count > 0:
                # Return updated application with details
                return self.get_application_with_details(application_id)
            return None
        except Exception as e:
            print(f"Error updating application {application_id}: {e}")
            return None

    def delete_application(self, application_id: str) -> bool:
        """
        Delete an application

        Args:
            application_id: String representation of MongoDB ObjectId

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(application_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting application {application_id}: {e}")
            return False


# Global repository instance
application_repository = ApplicationRepository()
