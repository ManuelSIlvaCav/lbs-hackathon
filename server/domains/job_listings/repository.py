"""
Repository for job listing operations
Uses the shared job_listings collection from CompanyRepository
"""

import logging
import time
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, UpdateOne, InsertOne, UpdateMany
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from urllib.parse import urlparse

from utils.singleton_class import SingletonMeta

from .models import (
    JobListingModel,
    JobListingCreate,
    JobListingUpdate,
    JobListingMetadata,
    JobListingOrigin,
)
from .source_repository import job_listing_source_repository
from database import get_collection
from integrations.agents.job_listing_parser import (
    AgentJobCategorizationSchema,
    JobCategorizationInput,
    run_agent_job_categorization,
)


logger = logging.getLogger("app")


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


class JobListingRepository(metaclass=SingletonMeta):
    """Repository for job listing CRUD operations using the shared job_listings collection"""

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        # Use the shared job_listings collection
        self.collection: Collection = get_collection("job_listings")
        # Create indexes for job listings
        self.collection.create_index("company_id")
        self.collection.create_index([("last_seen_at", DESCENDING), ("source_status")])
        self.collection.create_index([("origin", ASCENDING)])
        self.collection.create_index("url")  # Index for URL-based lookups
        self.collection.create_index("source_status")  # Index for status filtering
        self.collection.create_index([("updated_at", DESCENDING)])
        self.collection.create_index(
            [("profile_categories", 1), ("source_status", 1), ("last_seen_at", -1)],
        )

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

                categorization_input = JobCategorizationInput(
                    job_url=job_data.url, job_id=None
                )
                parsed_job = await run_agent_job_categorization(categorization_input)
                if parsed_job:
                    metadata = JobListingMetadata(categorization_schema=parsed_job)

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
                        "localField": "company_id",
                        "foreignField": "_id",
                        "as": "company_info_array",
                        "pipeline": [
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

    def get_job_listings_by_company(
        self,
        company_id: str,
        source_status: Optional[str] = None,
    ) -> List[JobListingModel]:
        """
        Get all job listings for a company

        Args:
            company_id: Company ID to filter by
            source_status: Optional filter by source status (enriched, scrapped, active, deactivated)

        Returns:
            List of JobListingModel objects
        """
        # Convert company_id string to ObjectId for query
        company_oid = (
            ObjectId(company_id) if isinstance(company_id, str) else company_id
        )

        # Build query filter
        query_filter = {"company_id": company_oid}
        if source_status:
            query_filter["source_status"] = source_status

        cursor = self.collection.find(query_filter).sort(
            "last_seen_at" if source_status == "enriched" else "deactivated_at", -1
        )

        job_listings = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            job_listings.append(JobListingModel(**doc))

        return job_listings

    def deactivate_job_listing(
        self,
        job_id: str,
    ) -> Optional[JobListingModel]:
        """
        Deactivate a job listing when parsing fails or job is no longer available

        Args:
            job_id: String representation of MongoDB ObjectId
            metadata: Optional agent metadata to store even for failed parsing

        Returns:
            Updated JobListingModel if successful, None otherwise
        """
        try:
            update_data = {
                "source_status": "deactivated",
                "deactivated_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(job_id)}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    "Job listing deactivated",
                    extra={
                        "context": "deactivate_job_listing",
                        "job_listing_id": job_id,
                    },
                )
                return self.get_job_listing_by_id(job_id)
            return None
        except Exception as e:
            logger.error(
                "Error deactivating job listing",
                extra={
                    "context": "deactivate_job_listing",
                    "job_listing_id": job_id,
                    "error_msg": str(e),
                },
            )
            return None

    def save_deactivation_souce_data(
        self, job_id: str, parsed_job: Optional[AgentJobCategorizationSchema] = None
    ):
        try:
            metadata = JobListingMetadata(
                categorization_schema=parsed_job, updated_at=datetime.now()
            )
            # Save metadata to job_listings_source if provided
            if metadata:
                try:
                    source = job_listing_source_repository.get_source_by_job_listing_id(
                        job_id
                    )
                    if source:
                        job_listing_source_repository.collection.update_one(
                            {"job_listing_id": ObjectId(job_id)},
                            {
                                "$set": {
                                    "sources.job_listing_agent": metadata.model_dump(
                                        mode="python"
                                    ),
                                    "updated_at": datetime.now(),
                                }
                            },
                        )
                    else:
                        from .source_models import JobListingSourceFieldModel

                        source_field = JobListingSourceFieldModel(
                            job_listing_agent=metadata
                        )
                        job_listing_source_repository.collection.insert_one(
                            {
                                "job_listing_id": ObjectId(job_id),
                                "sources": source_field.model_dump(mode="python"),
                                "created_at": datetime.now(),
                                "updated_at": datetime.now(),
                            }
                        )
                    logger.info(
                        "Stored agent metadata for deactivated job listing",
                        extra={
                            "context": "deactivate_job_listing",
                            "job_listing_id": job_id,
                        },
                    )
                except Exception as e:
                    logger.error(
                        "Error storing metadata for deactivated job",
                        extra={
                            "context": "deactivate_job_listing",
                            "job_listing_id": job_id,
                            "error_msg": str(e),
                        },
                    )
        except Exception as e:
            logger.error(
                "Error preparing metadata for deactivated job",
                extra={
                    "context": "deactivate_job_listing",
                    "job_listing_id": job_id,
                    "error_msg": str(e),
                },
            )

    async def enrich_job_listing(self, job_id: str) -> Optional[JobListingModel]:
        """
        Enrich a job listing by running the AI agent to extract structured data
        If parsing fails, deactivates the job listing

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

            categorization_input = JobCategorizationInput(
                job_url=job.url, job_id=job_id
            )
            parsed_job = await run_agent_job_categorization(categorization_input)

            date_now = datetime.now()

            if not parsed_job:
                logger.error(
                    "Failed to parse job description, deactivating job listing",
                    extra={
                        "context": "enrich_job_listings",
                        "job_listing_id": job_id,
                        "job_title": job.title,
                        "company_name": job.company,
                    },
                )
                # Deactivate the job listing since parsing failed (no metadata to store)
                return self.deactivate_job_listing(job_id)

            if (
                parsed_job.result == "no_longer_available"
                or parsed_job.result == "bad_format"
            ):
                logger.info(
                    "Job listing no longer available, deactivating job listing",
                    extra={
                        "context": "enrich_job_listings",
                        "job_listing_id": job_id,
                        "job_title": job.title,
                        "company_name": job.company,
                        "failed_result_error": (
                            parsed_job.failed_result_error
                            if hasattr(parsed_job, "failed_result_error")
                            else None
                        ),
                    },
                )

                # Deactivate and store the metadata showing why it failed
                deactivated_job_listing = self.deactivate_job_listing(job_id)
                self.save_deactivation_souce_data(job_id, parsed_job)
                return deactivated_job_listing
            # Successful parsing

            # Create metadata object for storage in sources
            metadata = JobListingMetadata(
                categorization_schema=parsed_job, updated_at=date_now
            )

            # Save metadata to job_listings_source collection
            # Get or create source document
            source = job_listing_source_repository.get_source_by_job_listing_id(job_id)

            if source:
                # Update existing source with agent metadata
                # Use mode='python' to properly serialize nested Pydantic models as dicts
                update_result = job_listing_source_repository.collection.update_one(
                    {"job_listing_id": ObjectId(job_id)},
                    {
                        "$set": {
                            "sources.job_listing_agent": metadata.model_dump(
                                mode="python"
                            ),
                            "updated_at": date_now,
                        }
                    },
                )
                logger.info(
                    "Updated job listing source with agent metadata",
                    extra={
                        "context": "enrich_job_listings",
                        "job_listing_id": job_id,
                        "modified_count": update_result.modified_count,
                    },
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
                            "job_listing_id": ObjectId(job_id),
                            "company_id": ObjectId(job.company_id),
                            "sources": source_field.model_dump(mode="python"),
                            "created_at": date_now,
                            "updated_at": date_now,
                        }
                    )

            # Update the job listing with enriched data (WITHOUT metadata)
            update_data = {
                "title": (
                    parsed_job.job_info.job_title
                    if parsed_job.job_info.job_title
                    else job.title
                ),
                "profile_categories": parsed_job.job_info.profile_categories,
                "role_titles": parsed_job.job_info.role_titles,
                "employement_type": parsed_job.job_info.employement_type,
                "work_arrangement": parsed_job.job_info.work_arrangement,
                "salary_range_min": parsed_job.job_info.salary_min,
                "salary_range_max": parsed_job.job_info.salary_max,
                "salary_currency": parsed_job.job_info.currency,
                "source_status": "enriched",
                "updated_at": date_now,
                "enriched_at": date_now,
            }

            result: UpdateResult = self.collection.update_one(
                {"_id": ObjectId(job_id)}, {"$set": update_data}
            )

            if result.modified_count == 0:
                logger.warning(
                    "No updates made to job listing after enrichment",
                    extra={
                        "context": "enrich_job_listings",
                        "job_listing_id": job_id,
                    },
                )

            # Return the updated job listing
            return self.get_job_listing_by_id(job_id)

        except Exception as e:
            logger.error(
                "Error enriching job listing",
                extra={
                    "context": "enrich_job_listings",
                    "job_listing_id": job_id,
                    "error": str(e),
                },
            )
            return None

    def upsert_job_listings_bulk(
        self,
        company_id: str,
        job_listings: List[JobListingCreate],
    ) -> tuple[List[str], List[str], int]:
        """
        Upsert multiple job listings in bulk with smart update logic using bulk_write:
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

        # Convert company_id to ObjectId for queries
        company_oid = (
            ObjectId(company_id) if isinstance(company_id, str) else company_id
        )

        # Get existing job listings for this company
        existing_jobs = self.collection.find(
            {"company_id": company_oid, "url": {"$exists": True}}
        )
        existing_jobs_map = {job["url"]: job for job in existing_jobs}

        # Collect all operations to execute in bulk
        bulk_operations = []
        inserted_ids = []  # Pre-track IDs for inserts
        updated_ids = []  # Pre-track IDs for updates

        # Process each job listing from provider
        for job_data in job_listings:
            if not job_data.url:
                continue

            existing_job = existing_jobs_map.get(job_data.url)

            if existing_job:
                # UPDATE: Build update operation for existing job
                update_fields = {
                    "updated_at": datetime.now(),
                }

                # Update posted_at if provided and different
                if job_data.posted_at:
                    update_fields["posted_at"] = job_data.posted_at

                if job_data.last_seen_at:
                    update_fields["last_seen_at"] = job_data.last_seen_at

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

                # Create UpdateOne operation
                bulk_operations.append(
                    UpdateOne({"_id": existing_job["_id"]}, {"$set": update_fields})
                )
                # Track this ID for the results
                updated_ids.append(str(existing_job["_id"]))

            else:
                # INSERT: Build insert operation for new job
                origin_domain = extract_domain(job_data.url)
                origin = determine_origin(origin_domain)

                job_dict = job_data.model_dump()
                # Convert company_id to ObjectId
                job_dict["company_id"] = (
                    ObjectId(company_id) if isinstance(company_id, str) else company_id
                )
                job_dict["created_at"] = datetime.now()
                job_dict["updated_at"] = datetime.now()
                job_dict["last_seen_at"] = datetime.now()
                job_dict["origin_domain"] = origin_domain
                job_dict["origin"] = origin

                # Pre-generate ObjectId to track inserted IDs
                new_id = ObjectId()
                job_dict["_id"] = new_id
                inserted_ids.append(str(new_id))

                # Create InsertOne operation with pre-assigned _id
                bulk_operations.append(InsertOne(job_dict))

        # Execute all operations in a single bulk_write
        if bulk_operations:
            self.collection.bulk_write(bulk_operations, ordered=False)

        # Execute expire operation separately to get accurate count
        # (bulk_write doesn't provide per-operation modified counts)
        expired_result = self.collection.update_many(
            {
                "company_id": company_oid,
                "url": {"$nin": list(current_urls), "$exists": True},
                "source_status": {"$eq": "enriched"},
            },
            {"$set": {"source_status": "expired", "updated_at": datetime.now()}},
        )
        expired_count = expired_result.modified_count

        return inserted_ids, updated_ids, expired_count

    def search_job_listings(
        self,
        company_id: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        origin: Optional[str] = None,
        profile_category: Optional[str] = None,
        role_title: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[JobListingModel], int]:
        """
        Search job listings with filters using MongoDB aggregation pipeline with $facet
        for efficient pagination. Uses round-robin distribution to mix companies and
        performs company lookup only on paginated results.

        Args:
            company_id: Optional company ID to filter by
            country: Optional country to filter by
            city: Optional city to filter by
            origin: Optional origin to filter by (linkedin, greenhouse, workday, careers)
            profile_category: Optional profile category to filter by
            role_title: Optional role title to filter by
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (list of JobListingModel objects, total count)
        """
        try:
            # Build match stage based on filters
            match_stage = {"source_status": {"$eq": "enriched"}}

            if company_id:
                # Convert company_id string to ObjectId for query
                match_stage["company_id"] = (
                    ObjectId(company_id) if isinstance(company_id, str) else company_id
                )

            if country:
                match_stage["country"] = country

            if city:
                match_stage["city"] = city

            if origin:
                match_stage["origin"] = origin

            if profile_category:
                # Use $in operator to match any value in the array
                match_stage["profile_categories"] = {"$in": [profile_category]}

            if role_title:
                # Use $in operator to match any value in the array
                match_stage["role_titles"] = {"$in": [role_title]}

            # Build aggregation pipeline
            pipeline = []

            # Add match stage if we have filters
            if match_stage:
                pipeline.append({"$match": match_stage})

            # Round-robin distribution: Use $setWindowFields to assign row numbers per company
            # This ensures jobs from different companies are mixed in the results
            pipeline.append(
                {
                    "$setWindowFields": {
                        "partitionBy": "$company_id",
                        "sortBy": {"last_seen_at": -1},
                        "output": {"company_row_num": {"$rank": {}}},
                    }
                }
            )

            # Sort by company_row_num first (distributes companies evenly),
            # then by last_seen_at (most recent within each round)
            pipeline.append({"$sort": {"company_row_num": 1, "last_seen_at": -1}})

            # Use $facet to get both count and paginated data efficiently
            # OPTIMIZATION: Company lookup is done AFTER pagination, only for returned records
            pipeline.append(
                {
                    "$facet": {
                        # Get total count before pagination
                        "metadata": [{"$count": "total"}],
                        # Paginate first, then lookup company info only for limited results
                        "data": [
                            {"$skip": skip},
                            {"$limit": limit},
                            # NOW lookup company info - only for the paginated results
                            {
                                "$lookup": {
                                    "from": "companies",
                                    "localField": "company_id",
                                    "foreignField": "_id",
                                    "as": "company_info_array",
                                    "pipeline": [
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
                                        }
                                    ],
                                }
                            },
                            # Convert company_info_array to single object
                            {
                                "$addFields": {
                                    "company_info": {
                                        "$cond": {
                                            "if": {
                                                "$gt": [
                                                    {"$size": "$company_info_array"},
                                                    0,
                                                ]
                                            },
                                            "then": {
                                                "$arrayElemAt": [
                                                    "$company_info_array",
                                                    0,
                                                ]
                                            },
                                            "else": None,
                                        }
                                    }
                                }
                            },
                            # Remove temporary fields
                            {
                                "$project": {
                                    "company_info_array": 0,
                                    "company_row_num": 0,
                                }
                            },
                        ],
                    }
                }
            )

            start = time.perf_counter()
            # Execute aggregation
            result = list(self.collection.aggregate(pipeline))
            request_time = time.perf_counter() - start

            logger.info(
                "Executing job listings search with round-robin distribution",
                extra={
                    "context": "JobListingRepository",
                    "pipeline": pipeline,
                    "skip": skip,
                    "limit": limit,
                    "filters": {
                        "company_id": company_id,
                        "country": country,
                        "city": city,
                        "origin": origin,
                        "profile_category": profile_category,
                        "role_title": role_title,
                    },
                    "request_time": f"{request_time * 1000:.0f} ms",
                },
            )

            if not result or len(result) == 0:
                return [], 0

            facet_result = result[0]

            # Extract total count
            total = (
                facet_result["metadata"][0]["total"] if facet_result["metadata"] else 0
            )

            # Extract and convert job listings
            job_listings = []
            for job in facet_result["data"]:
                job["_id"] = str(job["_id"])

                # Convert company_info._id to string if it exists
                if job.get("company_info") and job["company_info"].get("_id"):
                    job["company_info"]["_id"] = str(job["company_info"]["_id"])

                job_listings.append(JobListingModel(**job))

            return job_listings, total

        except Exception as e:
            logger.error(
                "Error searching job listings",
                extra={"context": "JobListingRepository", "error_msg": str(e)},
            )
            return [], 0

    def get_countries(self) -> List[str]:
        """
        Get all unique countries from enriched job listings

        Returns:
            Sorted list of unique country names
        """
        try:
            pipeline = [
                # Only consider enriched job listings
                {"$match": {"source_status": "enriched", "country": {"$ne": None}}},
                {"$group": {"_id": "$country"}},
                {"$sort": {"_id": 1}},
            ]

            results = list(self.collection.aggregate(pipeline))
            return [result["_id"] for result in results if result["_id"]]

        except Exception as e:
            logger.error(
                "Error getting countries",
                extra={"context": "JobListingRepository", "error_msg": str(e)},
            )
            return []

    def get_profile_categories(self) -> List[str]:
        """
        Get all unique profile categories from enriched job listings

        Returns:
            Sorted list of unique profile categories
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "source_status": "enriched",
                        "profile_categories": {"$ne": None},
                    }
                },
                {"$unwind": "$profile_categories"},
                {"$group": {"_id": "$profile_categories"}},
                {"$sort": {"_id": 1}},
            ]

            results = list(self.collection.aggregate(pipeline))
            return [result["_id"] for result in results if result["_id"]]

        except Exception as e:
            logger.error(
                "Error getting profile categories",
                extra={"context": "JobListingRepository", "error_msg": str(e)},
            )
            return []

    def get_role_titles(self) -> List[str]:
        """
        Get all unique role titles from enriched job listings

        Returns:
            Sorted list of unique role titles
        """
        try:
            pipeline = [
                {"$match": {"source_status": "enriched", "role_titles": {"$ne": None}}},
                {"$unwind": "$role_titles"},
                {"$group": {"_id": "$role_titles"}},
                {"$sort": {"_id": 1}},
            ]

            results = list(self.collection.aggregate(pipeline))
            return [result["_id"] for result in results if result["_id"]]

        except Exception as e:
            logger.error(
                "Error getting role titles",
                extra={"context": "JobListingRepository", "error_msg": str(e)},
            )
            return []


# Singleton instance
job_listing_repository = JobListingRepository()
