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
        self.collection.create_index("url")  # Index for URL-based lookups

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
        Get a job listing by ID with company information

        Args:
            job_id: String representation of MongoDB ObjectId

        Returns:
            JobListingModel if found, None otherwise
        """
        try:
            # Use aggregation to include company lookup
            pipeline = [
                {"$match": {"_id": ObjectId(job_id)}},
                {
                    "$lookup": {
                        "from": "companies",
                        "let": {"company_id_str": {"$toString": "$company_id"}},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [
                                            {"$toString": "$_id"},
                                            "$$company_id_str",
                                        ]
                                    }
                                }
                            },
                            {
                                "$project": {
                                    "_id": 1,
                                    "name": 1,
                                    "company_url": 1,
                                    "linkedin_url": 1,
                                    "logo_url": 1,
                                    "domain": 1,
                                    "industries": 1,
                                    "description": 1,
                                }
                            },
                        ],
                        "as": "company_info_array",
                    }
                },
                {
                    "$addFields": {
                        "company_info": {
                            "$cond": {
                                "if": {"$gt": [{"$size": "$company_info_array"}, 0]},
                                "then": {"$arrayElemAt": ["$company_info_array", 0]},
                                "else": None,
                            }
                        }
                    }
                },
                {"$project": {"company_info_array": 0}},
            ]

            result = list(self.collection.aggregate(pipeline))

            if result:
                job = result[0]
                job["_id"] = str(job["_id"])

                # Convert company_info._id to string if it exists
                if job.get("company_info") and job["company_info"].get("_id"):
                    job["company_info"]["_id"] = str(job["company_info"]["_id"])

                return JobListingModel(**job)

            return None
        except Exception as e:
            print(f"Error getting job listing: {e}")
            return None

    def get_all_job_listings(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[JobListingModel]:
        """
        Get all job listings with pagination and optional status filter, including company info

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter ("active", "archived", etc.)

        Returns:
            List of JobListingModel objects
        """
        # Build aggregation pipeline
        pipeline = []

        # Add match stage if status filter exists
        if status:
            pipeline.append({"$match": {"status": status}})

        # Sort by most recent first
        pipeline.append({"$sort": {"created_at": -1}})

        # Skip and limit
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        # Add $lookup stage to join company information
        pipeline.append(
            {
                "$lookup": {
                    "from": "companies",
                    "let": {"company_id_str": {"$toString": "$company_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$company_id_str"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "name": 1,
                                "company_url": 1,
                                "linkedin_url": 1,
                                "logo_url": 1,
                                "domain": 1,
                                "industries": 1,
                                "description": 1,
                            }
                        },
                    ],
                    "as": "company_info_array",
                }
            }
        )

        # Convert company_info_array to single object
        pipeline.append(
            {
                "$addFields": {
                    "company_info": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$company_info_array"}, 0]},
                            "then": {"$arrayElemAt": ["$company_info_array", 0]},
                            "else": None,
                        }
                    }
                }
            }
        )

        # Remove the temporary array field
        pipeline.append({"$project": {"company_info_array": 0}})

        # Execute aggregation
        job_listings = []
        for job in self.collection.aggregate(pipeline):
            job["_id"] = str(job["_id"])

            # Convert company_info._id to string if it exists
            if job.get("company_info") and job["company_info"].get("_id"):
                job["company_info"]["_id"] = str(job["company_info"]["_id"])

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
        self,
        company_id: str,
    ) -> List[JobListingModel]:
        """
        Get all job listings for a company

        Args:
            company_id: Company ID to filter by

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

    def upsert_job_listings_bulk(
        self,
        company_id: str,
        job_listings: List[JobListingCreate],
    ) -> tuple[List[str], List[str], int]:
        """
        Upsert multiple job listings in bulk with smart update logic:
        - New jobs (by URL): Insert
        - Existing jobs (by URL): Update last_seen_at and posted_at
        - Missing jobs: Mark as expired (not in current response)

        Args:
            company_id: Company ID to filter by
            job_listings: List of JobListingCreate objects from provider

        Returns:
            tuple: (list of inserted IDs, list of updated IDs, count of expired jobs)
        """
        if not job_listings:
            return [], [], 0

        # Get current job URLs from provider response
        current_urls = {job.url for job in job_listings if job.url}

        # Get existing job listings for this company
        existing_jobs = self.collection.find(
            {"company_id": company_id, "url": {"$exists": True}}
        )
        existing_jobs_map = {job["url"]: job for job in existing_jobs}

        inserted_ids = []
        updated_ids = []

        # Process each job listing from provider
        for job_data in job_listings:
            if not job_data.url:
                continue

            # Extract origin fields
            existing_job = existing_jobs_map.get(job_data.url)

            if existing_job:
                # UPDATE: Job already exists, update timestamps
                update_fields = {
                    "last_seen_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "status": "active",  # Reactivate if it was expired
                }

                # Update posted_at if provided and different
                if job_data.posted_at:
                    update_fields["posted_at"] = job_data.posted_at

                # Update other fields if they've changed
                if job_data.title and job_data.title != existing_job.get("title"):
                    update_fields["title"] = job_data.title
                if job_data.location and job_data.location != existing_job.get(
                    "location"
                ):
                    update_fields["location"] = job_data.location
                if job_data.city:
                    update_fields["city"] = job_data.city
                if job_data.state:
                    update_fields["state"] = job_data.state
                if job_data.country:
                    update_fields["country"] = job_data.country

                result = self.collection.update_one(
                    {"_id": existing_job["_id"]}, {"$set": update_fields}
                )

                if result.modified_count > 0:
                    updated_ids.append(str(existing_job["_id"]))

            else:
                origin_domain = extract_domain(job_data.url)
                origin = determine_origin(origin_domain)
                # INSERT: New job listing
                job_dict = job_data.model_dump()
                job_dict["company_id"] = company_id
                job_dict["created_at"] = datetime.now()
                job_dict["updated_at"] = datetime.now()
                job_dict["last_seen_at"] = datetime.now()
                job_dict["status"] = "active"
                job_dict["origin_domain"] = origin_domain
                job_dict["origin"] = origin

                result = self.collection.insert_one(job_dict)
                inserted_ids.append(str(result.inserted_id))

        # EXPIRE: Mark jobs not in current response as expired
        # Only expire jobs that are currently active
        expired_result = self.collection.update_many(
            {
                "company_id": company_id,
                "url": {"$nin": list(current_urls), "$exists": True},
                "status": "active",
            },
            {"$set": {"status": "expired", "updated_at": datetime.now()}},
        )

        expired_count = expired_result.modified_count

        return inserted_ids, updated_ids, expired_count

    def get_job_listing_by_url(
        self, url: str, company_id: Optional[str] = None
    ) -> Optional[JobListingModel]:
        """
        Get a job listing by URL

        Args:
            url: Job listing URL
            company_id: Optional company_id to narrow search

        Returns:
            JobListingModel if found, None otherwise
        """
        try:
            query = {"url": url}
            if company_id:
                query["company_id"] = company_id

            job = self.collection.find_one(query)
            if job:
                job["_id"] = str(job["_id"])
                return JobListingModel(**job)
            return None
        except Exception as e:
            print(f"Error getting job listing by URL: {e}")
            return None

    def search_job_listings(
        self,
        company_id: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        origin: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[JobListingModel], int]:
        """
        Search job listings with filters using MongoDB aggregation pipeline with $facet
        for efficient pagination following best practices. Includes company information via $lookup.

        Args:
            company_id: Optional company ID to filter by
            country: Optional country to filter by
            city: Optional city to filter by
            origin: Optional origin to filter by (linkedin, greenhouse, workday, careers)
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (list of JobListingModel objects, total count)
        """
        # Build match stage based on filters
        match_stage = {}

        if company_id:
            match_stage["company_id"] = company_id

        if country:
            match_stage["country"] = country

        if city:
            match_stage["city"] = city

        if origin:
            match_stage["origin"] = origin

        # Build aggregation pipeline with $facet for efficient pagination
        pipeline = []

        # Add match stage if we have filters
        if match_stage:
            pipeline.append({"$match": match_stage})

        # Add sort stage (most recent first)
        pipeline.append({"$sort": {"created_at": -1}})

        # Add $lookup stage to join company information
        pipeline.append(
            {
                "$lookup": {
                    "from": "companies",
                    "let": {"company_id_str": {"$toString": "$company_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$company_id_str"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "name": 1,
                                "company_url": 1,
                                "linkedin_url": 1,
                                "logo_url": 1,
                                "domain": 1,
                                "industries": 1,
                                "description": 1,
                            }
                        },
                    ],
                    "as": "company_info_array",
                }
            }
        )

        # Convert company_info_array to single object (or null if empty)
        pipeline.append(
            {
                "$addFields": {
                    "company_info": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$company_info_array"}, 0]},
                            "then": {"$arrayElemAt": ["$company_info_array", 0]},
                            "else": None,
                        }
                    }
                }
            }
        )

        # Remove the temporary array field
        pipeline.append({"$project": {"company_info_array": 0}})

        # Use $facet to get both data and count in one query
        pipeline.append(
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [{"$skip": skip}, {"$limit": limit}],
                }
            }
        )

        # Execute aggregation
        result = list(self.collection.aggregate(pipeline))

        if not result or len(result) == 0:
            return [], 0

        facet_result = result[0]

        # Extract total count
        total = facet_result["metadata"][0]["total"] if facet_result["metadata"] else 0

        # Extract and convert job listings
        job_listings = []
        for job in facet_result["data"]:
            job["_id"] = str(job["_id"])

            # Convert company_info._id to string if it exists
            if job.get("company_info") and job["company_info"].get("_id"):
                job["company_info"]["_id"] = str(job["company_info"]["_id"])

            job_listings.append(JobListingModel(**job))

        return job_listings, total


# Singleton instance
job_listing_repository = JobListingRepository()
