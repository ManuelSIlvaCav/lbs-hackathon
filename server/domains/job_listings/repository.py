"""
Repository for job listing operations
Uses the shared job_listings collection from CompanyRepository
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from .models import (
    JobListingModel,
    JobListingCreate,
    JobListingUpdate,
    JobListingResponse,
    JobListingMetadata,
)
from .source_models import ProviderSourceInfo
from .source_repository import job_listing_source_repository
from database import get_collection
from integrations.agents.job_listing_parser_agent import (
    JobCategorizationInput,
    run_agent_job_categorization,
)


class JobListingRepository:
    """Repository for job listing CRUD operations using the shared job_listings collection"""

    def __init__(self):
        # Use the shared job_listings collection
        self.collection: Collection = get_collection("job_listings")
        # Create indexes for job listings
        self.collection.create_index("company_id")
        self.collection.create_index("job_enrichment_id")
        self.collection.create_index("provider_job_id")
        self.collection.create_index("last_seen_at")

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

    def save_job_listing(self, job_data: JobListingCreate) -> str:
        """
        Save a single job listing (used by enrichment system)
        Also creates/updates source tracking for the provider

        Args:
            job_data: JobListingCreate object with job information

        Returns:
            String ID of the inserted job listing
        """
        job_dict = job_data.model_dump()
        job_dict["created_at"] = datetime.now()

        result = self.collection.insert_one(job_dict)
        job_listing_id = str(result.inserted_id)

        # Create source tracking if provider information is available
        if job_data.provider and job_data.provider_job_id and job_data.company_id:
            try:
                provider_info = ProviderSourceInfo(
                    job_enrichment_id=job_data.job_enrichment_id,
                    provider_job_id=job_data.provider_job_id,
                    url=job_data.url,
                    first_seen_at=datetime.now(),
                    last_seen_at=job_data.last_seen_at or datetime.now(),
                )
                job_listing_source_repository.add_or_update_provider_source(
                    job_listing_id=job_listing_id,
                    company_id=job_data.company_id,
                    provider_name=job_data.provider,
                    provider_info=provider_info,
                )
            except Exception as e:
                print(f"Warning: Failed to create source tracking: {e}")
                # Continue even if source tracking fails

        return job_listing_id

    def save_job_listings_bulk(self, job_listings: List[JobListingCreate]) -> List[str]:
        """
        Save multiple job listings in bulk (used by enrichment system)
        Also creates/updates source tracking for each job

        Args:
            job_listings: List of JobListingCreate objects

        Returns:
            List of string IDs of the inserted job listings
        """
        if not job_listings:
            return []

        jobs_to_insert = []
        for job_data in job_listings:
            job_dict = job_data.model_dump()
            job_dict["created_at"] = datetime.now()
            jobs_to_insert.append(job_dict)

        result = self.collection.insert_many(jobs_to_insert)
        job_listing_ids = [str(id) for id in result.inserted_ids]

        # Create source tracking for all job listings in bulk
        sources_data = []
        for idx, job_data in enumerate(job_listings):
            if job_data.provider and job_data.provider_job_id and job_data.company_id:
                provider_info = ProviderSourceInfo(
                    job_enrichment_id=job_data.job_enrichment_id,
                    provider_job_id=job_data.provider_job_id,
                    url=job_data.url,
                    first_seen_at=datetime.now(),
                    last_seen_at=job_data.last_seen_at or datetime.now(),
                )
                sources_data.append(
                    {
                        "job_listing_id": job_listing_ids[idx],
                        "company_id": job_data.company_id,
                        "provider_name": job_data.provider,
                        "provider_info": provider_info,
                    }
                )

        if sources_data:
            try:
                count = (
                    job_listing_source_repository.add_or_update_provider_sources_bulk(
                        sources_data
                    )
                )
                print(f"Created {count} source tracking records")
            except Exception as e:
                print(f"Warning: Failed to create source tracking in bulk: {e}")
                # Continue even if source tracking fails

        return job_listing_ids

    def get_job_listings_by_company(
        self, company_id: str, provider: str = "apollo"
    ) -> List[JobListingResponse]:
        """
        Get all job listings for a company

        Args:
            company_id: Company ID to filter by
            provider: Provider to filter by (default: "apollo")

        Returns:
            List of JobListingResponse objects
        """
        cursor = self.collection.find(
            {"company_id": company_id, "provider": provider}
        ).sort("last_seen_at", -1)

        job_listings = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            job_listings.append(JobListingResponse(**doc))

        return job_listings

    def get_job_listings_by_enrichment(
        self, job_enrichment_id: str
    ) -> List[JobListingResponse]:
        """
        Get all job listings for a specific enrichment

        Args:
            job_enrichment_id: Job enrichment ID to filter by

        Returns:
            List of JobListingResponse objects
        """
        cursor = self.collection.find({"job_enrichment_id": job_enrichment_id})

        job_listings = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            job_listings.append(JobListingResponse(**doc))

        return job_listings


# Singleton instance
job_listing_repository = JobListingRepository()
