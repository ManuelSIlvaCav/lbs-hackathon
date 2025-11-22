"""
Repository for job listing operations
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from models.job_listings import (
    JobListingModel,
    JobListingCreate,
    JobListingUpdate,
    JobListingResponse,
    JobListingMetadata,
)
from database import get_collection
from integrations.agents.job_listing_parser_agent import (
    JobCategorizationInput,
    run_agent_job_categorization,
)


class JobListingRepository:
    """Repository for job listing CRUD operations"""

    def __init__(self):
        self.collection: Collection = get_collection("job_listings")

    async def create_job_listing(
        self, job_data: JobListingCreate
    ) -> JobListingResponse:
        """
        Create a new job listing in the database

        Args:
            job_data: JobListingCreate object with job information

        Returns:
            JobListingResponse object with created job listing data including ID
        """
        # Parse job description if available
        metadata = None
        if job_data.url:
            try:
                print(f"Parsing job description for: {job_data.title or job_data.url}")
                categorization_input = JobCategorizationInput(job_url=job_data.url)
                parsed_job = await run_agent_job_categorization(categorization_input)
                if parsed_job:
                    metadata = JobListingMetadata(categorization_schema=parsed_job)
                    print(f"Job parsing successful: {parsed_job.job_info.job_title}")
            except Exception as e:
                print(f"Error parsing job description: {e}")
                # Continue without metadata if parsing fails

        # Create job listing model with timestamps
        job_listing = JobListingModel(
            url=job_data.url,
            title=job_data.title,
            company=job_data.company,
            location=job_data.location,
            description=job_data.description,
            metadata=metadata,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion (exclude id field)
        job_dict = job_listing.model_dump(by_alias=True, exclude=["id"])

        # Insert into database
        result: InsertOneResult = self.collection.insert_one(job_dict)

        # Retrieve the inserted document
        inserted_job = self.collection.find_one({"_id": result.inserted_id})

        if not inserted_job:
            raise ValueError("Failed to retrieve inserted job listing")

        # Convert ObjectId to string for response
        inserted_job["_id"] = str(inserted_job["_id"])

        return JobListingResponse(**inserted_job)

    def get_job_listing_by_id(self, job_id: str) -> Optional[JobListingResponse]:
        """
        Get a job listing by ID

        Args:
            job_id: String representation of MongoDB ObjectId

        Returns:
            JobListingResponse if found, None otherwise
        """
        try:
            job = self.collection.find_one({"_id": ObjectId(job_id)})
            if job:
                job["_id"] = str(job["_id"])
                return JobListingResponse(**job)
            return None
        except Exception as e:
            print(f"Error getting job listing: {e}")
            return None

    def get_all_job_listings(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[JobListingResponse]:
        """
        Get all job listings with pagination and optional status filter

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter ("active", "archived", etc.)

        Returns:
            List of JobListingResponse objects
        """
        job_listings = []

        # Build query filter
        query = {}
        if status:
            query["status"] = status

        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        )

        for job in cursor:
            job["_id"] = str(job["_id"])
            job_listings.append(JobListingResponse(**job))

        return job_listings

    def update_job_listing(
        self, job_id: str, job_data: JobListingUpdate
    ) -> Optional[JobListingResponse]:
        """
        Update a job listing

        Args:
            job_id: String representation of MongoDB ObjectId
            job_data: JobListingUpdate object with updated data (all fields optional)

        Returns:
            Updated JobListingResponse if successful, None otherwise
        """
        try:
            # Only include fields that were actually set (not None)
            update_data = job_data.model_dump(exclude_unset=True, exclude_none=True)

            # If there's nothing to update, return the current job listing
            if not update_data:
                return self.get_job_listing_by_id(job_id)

            # Always update the updated_at timestamp
            update_data["updated_at"] = datetime.now()

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(job_id)}, {"$set": update_data}
            )

            if result.matched_count > 0:
                return self.get_job_listing_by_id(job_id)
            return None
        except Exception as e:
            print(f"Error updating job listing: {e}")
            return None

    def delete_job_listing(self, job_id: str) -> bool:
        """
        Delete a job listing

        Args:
            job_id: String representation of MongoDB ObjectId

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result: DeleteResult = self.collection.delete_one({"_id": ObjectId(job_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting job listing: {e}")
            return False

    def get_job_listing_count(self, status: Optional[str] = None) -> int:
        """
        Get total count of job listings

        Args:
            status: Optional status filter

        Returns:
            Total number of job listings
        """
        query = {}
        if status:
            query["status"] = status
        return self.collection.count_documents(query)


# Singleton instance
job_listing_repository = JobListingRepository()
