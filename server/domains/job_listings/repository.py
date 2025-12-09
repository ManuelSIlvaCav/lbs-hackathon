"""
Repository for job listing operations
Uses the shared job_listings collection from CompanyRepository
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from urllib.parse import urlparse

from .models import (
    JobListingModel,
    JobListingCreate,
    JobListingUpdate,
    JobListingMetadata,
    JobListingOrigin,
)
from .source_repository import job_listing_source_repository
from database import get_collection
from integrations.agents.job_listing_parser_agent import (
    JobCategorizationInput,
    run_agent_job_categorization,
)


def extract_domain(url: str) -> str:
    """
    Extract domain from URL, removing 'www.' prefix if present

    Args:
        url: Full URL string

    Returns:
        Domain string (e.g., 'linkedin.com', 'greenhouse.io')
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove 'www.' prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def determine_origin(domain: str) -> str:
    """
    Determine the origin type based on the domain

    Args:
        domain: Domain string

    Returns:
        Origin string (linkedin, greenhouse, workday, careers, other)
    """
    domain_lower = domain.lower()

    if "linkedin" in domain_lower:
        return JobListingOrigin.LINKEDIN.value
    elif "greenhouse" in domain_lower:
        return JobListingOrigin.GREENHOUSE.value
    elif "workday" in domain_lower:
        return JobListingOrigin.WORKDAY.value
    else:
        return JobListingOrigin.CAREERS.value


class JobListingRepository:
    """Repository for job listing CRUD operations using the shared job_listings collection"""

    def __init__(self):
        # Use the shared job_listings collection
        self.collection: Collection = get_collection("job_listings")
        # Create indexes for job listings
        self.collection.create_index("company_id")
        self.collection.create_index("last_seen_at")
        self.collection.create_index([("origin", ASCENDING)])

    async def create_job_listing(self, job_data: JobListingCreate) -> JobListingModel:
        """
        Create a new job listing in the database

        Args:
            job_data: JobListingCreate object with job information

        Returns:
            JobListingModel object with created job listing data including ID
        """
        # Parse job description if available
        metadata = None
        parsed_job = None
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

        # Create job listing model with timestamps (WITHOUT metadata)
        job_listing = JobListingModel(
            url=job_data.url,
            title=job_data.title,
            company=job_data.company,
            location=job_data.location,
            description=job_data.description,
            profile_categories=(
                parsed_job.job_info.profile_categories if parsed_job else None
            ),
            role_titles=parsed_job.job_info.role_titles if parsed_job else None,
            employement_type=(
                parsed_job.job_info.employement_type if parsed_job else None
            ),
            work_arrangement=(
                parsed_job.job_info.work_arrangement if parsed_job else None
            ),
            source_status="enriched" if metadata else "scrapped",
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion (exclude id field)
        job_dict = job_listing.model_dump(by_alias=True, exclude=["id"])

        # Insert into database
        result: InsertOneResult = self.collection.insert_one(job_dict)
        job_id = str(result.inserted_id)

        # Save metadata to job_listings_source if available
        if metadata and job_data.company_id:
            try:
                from .source_models import JobListingSourceFieldModel

                source_field = JobListingSourceFieldModel(job_listing_agent=metadata)

                job_listing_source_repository.collection.insert_one(
                    {
                        "job_listing_id": job_id,
                        "company_id": job_data.company_id,
                        "sources": source_field.model_dump(mode="python"),
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                )
                print(
                    f"Created job_listings_source with agent metadata for new job {job_id}"
                )
            except Exception as e:
                print(
                    f"Warning: Could not create source document for job {job_id}: {e}"
                )

        # Retrieve the inserted document
        inserted_job = self.collection.find_one({"_id": result.inserted_id})

        if not inserted_job:
            raise ValueError("Failed to retrieve inserted job listing")

        # Convert ObjectId to string for response
        inserted_job["_id"] = str(inserted_job["_id"])

        return JobListingModel(**inserted_job)

    def get_job_listing_by_id(self, job_id: str) -> Optional[JobListingModel]:
        """
        Get a job listing by ID

        Args:
            job_id: String representation of MongoDB ObjectId

        Returns:
            JobListingModel if found, None otherwise
        """
        try:
            job = self.collection.find_one({"_id": ObjectId(job_id)})
            if job:
                job["_id"] = str(job["_id"])
                return JobListingModel(**job)
            return None
        except Exception as e:
            print(f"Error getting job listing: {e}")
            return None

    def get_all_job_listings(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[JobListingModel]:
        """
        Get all job listings with pagination and optional status filter

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter ("active", "archived", etc.)

        Returns:
            List of JobListingModel objects
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
            job_listings.append(JobListingModel(**job))

        return job_listings

    def update_job_listing(
        self, job_id: str, job_data: JobListingUpdate
    ) -> Optional[JobListingModel]:
        """
        Update a job listing

        Args:
            job_id: String representation of MongoDB ObjectId
            job_data: JobListingUpdate object with updated data (all fields optional)

        Returns:
            Updated JobListingModel if successful, None otherwise
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
        Note: Source tracking must be done separately via JobListingSourceRepository

        Args:
            job_data: JobListingCreate object with job information

        Returns:
            String ID of the inserted job listing
        """
        job_dict = job_data.model_dump()
        job_dict["created_at"] = datetime.now()

        # Extract and set origin fields
        if job_data.url:
            origin_domain = extract_domain(job_data.url)
            origin = determine_origin(origin_domain)
            job_dict["origin_domain"] = origin_domain
            job_dict["origin"] = origin

        result = self.collection.insert_one(job_dict)
        job_listing_id = str(result.inserted_id)

        return job_listing_id

    def save_job_listings_bulk(self, job_listings: List[JobListingCreate]) -> List[str]:
        """
        Save multiple job listings in bulk (used by enrichment system)
        Note: Source tracking must be done separately via JobListingSourceRepository

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

            # Extract and set origin fields
            if job_data.url:
                origin_domain = extract_domain(job_data.url)
                origin = determine_origin(origin_domain)
                job_dict["origin_domain"] = origin_domain
                job_dict["origin"] = origin

            jobs_to_insert.append(job_dict)

        result = self.collection.insert_many(jobs_to_insert)
        job_listing_ids = [str(id) for id in result.inserted_ids]

        return job_listing_ids

    def get_job_listings_by_company(
        self, company_id: str, provider: str = "apollo"
    ) -> List[JobListingModel]:
        """
        Get all job listings for a company

        Args:
            company_id: Company ID to filter by
            provider: Provider to filter by (default: "apollo")

        Returns:
            List of JobListingModel objects
        """
        cursor = self.collection.find({"company_id": company_id}).sort(
            "last_seen_at", -1
        )

        job_listings = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            job_listings.append(JobListingModel(**doc))

        return job_listings

    def get_job_listings_by_enrichment(
        self, job_enrichment_id: str
    ) -> List[JobListingModel]:
        """
        Get all job listings for a specific enrichment

        Args:
            job_enrichment_id: Job enrichment ID to filter by

        Returns:
            List of JobListingModel objects
        """
        cursor = self.collection.find({"job_enrichment_id": job_enrichment_id})

        job_listings = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            job_listings.append(JobListingModel(**doc))

        return job_listings

    async def enrich_job_listing(self, job_id: str) -> Optional[JobListingModel]:
        """
        Enrich a job listing by running the AI agent to extract structured data

        Args:
            job_id: String representation of MongoDB ObjectId

        Returns:
            Updated JobListingModel if successful, None otherwise
        """
        try:
            # Get the existing job listing
            job = self.get_job_listing_by_id(job_id)
            if not job:
                print(f"Job listing not found: {job_id}")
                return None

            # Run the agent to extract structured data
            print(f"Enriching job listing: {job.title} ({job_id})")
            categorization_input = JobCategorizationInput(job_url=job.url)
            parsed_job = await run_agent_job_categorization(categorization_input)

            if not parsed_job:
                print(f"Failed to parse job description for: {job_id}")
                return None

            # Print the agent result
            print("=" * 80)
            print("AGENT ENRICHMENT RESULT:")
            print(f"Job ParsedData: {parsed_job}")
            print(f"Job Title: {parsed_job.job_info.job_title}")
            print(f"Profile Categories: {parsed_job.job_info.profile_categories}")
            print(f"Role Titles: {parsed_job.job_info.role_titles}")
            print(f"Employment Type: {parsed_job.job_info.employement_type}")
            print(f"Work Arrangement: {parsed_job.job_info.work_arrangement}")
            print(f"Description Summary: {parsed_job.description_summary}")
            print("=" * 80)

            # Create metadata object for storage in sources
            metadata = JobListingMetadata(categorization_schema=parsed_job)

            # Save metadata to job_listings_source collection
            # Get or create source document
            source = job_listing_source_repository.get_source_by_job_listing_id(job_id)

            if source:
                # Update existing source with agent metadata
                # Use mode='python' to properly serialize nested Pydantic models as dicts
                update_result = job_listing_source_repository.collection.update_one(
                    {"job_listing_id": job_id},
                    {
                        "$set": {
                            "sources.job_listing_agent": metadata.model_dump(
                                mode="python"
                            ),
                            "updated_at": datetime.now(),
                        }
                    },
                )
                print(
                    f"Updated job_listings_source with agent metadata for job {job_id} and result: {update_result}"
                )
            else:
                # Create new source document with agent metadata
                if job.company_id:
                    from .source_models import JobListingSourceFieldModel

                    source_field = JobListingSourceFieldModel(
                        job_listing_agent=metadata
                    )

                    # Use mode='python' to properly serialize nested Pydantic models as dicts
                    job_listing_source_repository.collection.insert_one(
                        {
                            "job_listing_id": job_id,
                            "company_id": job.company_id,
                            "sources": source_field.model_dump(mode="python"),
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                        }
                    )
                    print(
                        f"Created new job_listings_source with agent metadata for job {job_id}"
                    )

            # Update the job listing with enriched data (WITHOUT metadata)
            update_data = {
                "profile_categories": parsed_job.job_info.profile_categories,
                "role_titles": parsed_job.job_info.role_titles,
                "employement_type": parsed_job.job_info.employement_type,
                "work_arrangement": parsed_job.job_info.work_arrangement,
                "salary_range_min": parsed_job.job_info.salary_min,
                "salary_range_max": parsed_job.job_info.salary_max,
                "salary_currency": parsed_job.job_info.currency,
                "source_status": "enriched",
                "updated_at": datetime.now(),
            }

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(job_id)}, {"$set": update_data}
            )

            if result.modified_count == 0:
                print(f"No changes made to job listing: {job_id}")

            # Return the updated job listing
            return self.get_job_listing_by_id(job_id)

        except Exception as e:
            print(f"Error enriching job listing {job_id}: {e}")
            return None


# Singleton instance
job_listing_repository = JobListingRepository()
