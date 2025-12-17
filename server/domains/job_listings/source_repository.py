"""
Repository for job listing source operations
Tracks job listings across multiple providers/sources
"""

from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo import UpdateOne, InsertOne

from .source_models import (
    JobListingSourceModel,
    JobListingSourceCreate,
    JobListingSourceResponse,
    ApolloProviderSourceInfo,
)
from database import get_collection


class JobListingSourceRepository:
    """Repository for job listing source tracking operations"""

    def __init__(self):
        self.collection: Collection = get_collection("job_listings_source")
        # Create indexes
        self.collection.create_index("job_listing_id", unique=True)
        self.collection.create_index("company_id")
        self.collection.create_index([("job_listing_id", 1), ("company_id", 1)])

    def create_source(
        self, source_data: JobListingSourceCreate
    ) -> JobListingSourceResponse:
        """
        Create a new job listing source tracking document

        Args:
            source_data: JobListingSourceCreate object

        Returns:
            JobListingSourceResponse object with created source data
        """
        # Convert IDs to ObjectId if they're strings
        job_listing_oid = (
            ObjectId(source_data.job_listing_id)
            if isinstance(source_data.job_listing_id, str)
            else source_data.job_listing_id
        )
        company_oid = (
            ObjectId(source_data.company_id)
            if isinstance(source_data.company_id, str)
            else source_data.company_id
        )

        source_model = JobListingSourceModel(
            job_listing_id=job_listing_oid,
            company_id=company_oid,
            sources=source_data.sources,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        source_dict = source_model.model_dump(by_alias=True, exclude=["id"])
        result = self.collection.insert_one(source_dict)

        inserted_source = self.collection.find_one({"_id": result.inserted_id})
        if not inserted_source:
            raise ValueError("Failed to retrieve inserted source")

        inserted_source["_id"] = str(inserted_source["_id"])
        return JobListingSourceResponse(**inserted_source)

    def get_source_by_job_listing_id(
        self, job_listing_id: str
    ) -> Optional[JobListingSourceResponse]:
        """
        Get source tracking for a specific job listing

        Args:
            job_listing_id: Job listing ID to look up (string representation)

        Returns:
            JobListingSourceResponse if found, None otherwise
        """
        try:
            # Convert to ObjectId for query
            job_listing_oid = (
                ObjectId(job_listing_id)
                if isinstance(job_listing_id, str)
                else job_listing_id
            )
            source = self.collection.find_one({"job_listing_id": job_listing_oid})
            if source:
                source["_id"] = str(source["_id"])
                return JobListingSourceResponse(**source)
            return None
        except Exception as e:
            print(f"Error getting job listing source: {e}")
            return None

    def get_sources_by_company(self, company_id: str) -> List[JobListingSourceResponse]:
        """
        Get all source tracking documents for a company

        Args:
            company_id: Company ID to filter by (string representation)

        Returns:
            List of JobListingSourceResponse objects
        """
        # Convert to ObjectId for query
        company_oid = (
            ObjectId(company_id) if isinstance(company_id, str) else company_id
        )
        cursor = self.collection.find({"company_id": company_oid})
        sources = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            sources.append(JobListingSourceResponse(**doc))
        return sources

    def add_or_update_provider_source(
        self,
        job_listing_id: str,
        company_id: str,
        provider_name: str,
        provider_info: ApolloProviderSourceInfo,
    ) -> JobListingSourceResponse:
        """
        Add or update a provider source for a job listing
        Creates the source document if it doesn't exist

        Args:
            job_listing_id: Job listing ID (string representation)
            company_id: Company ID (string representation)
            provider_name: Name of the provider (e.g., 'apollo', 'linkedin')
            provider_info: Provider source information

        Returns:
            Updated JobListingSourceResponse
        """
        # Convert to ObjectId for query
        job_listing_oid = (
            ObjectId(job_listing_id)
            if isinstance(job_listing_id, str)
            else job_listing_id
        )
        company_oid = (
            ObjectId(company_id) if isinstance(company_id, str) else company_id
        )

        # Try to find existing source document
        existing = self.collection.find_one({"job_listing_id": job_listing_oid})

        if existing:
            # Update existing document
            update_data = {
                f"sources.{provider_name}": provider_info.model_dump(),
                "updated_at": datetime.now(),
            }
            self.collection.update_one(
                {"job_listing_id": job_listing_oid}, {"$set": update_data}
            )
        else:
            # Create new document with ObjectId
            source_data = JobListingSourceCreate(
                job_listing_id=job_listing_oid,
                company_id=company_oid,
                sources={provider_name: provider_info},
            )
            return self.create_source(source_data)

        # Return updated document (pass string for get method)
        result = self.get_source_by_job_listing_id(str(job_listing_oid))
        if not result:
            raise ValueError("Failed to retrieve updated source")
        return result

    def sync_provider_sources_for_jobs(
        self,
        inserted_ids: List[str],
        updated_ids: List[str],
        company_id: str,
        provider_name: str,
        job_enrichment_id: str,
        url_to_provider_data: Dict[str, Dict[str, any]],
    ) -> int:
        """
        Sync provider sources for inserted and updated job listings
        Optimized to fetch all jobs in bulk instead of individual queries

        Args:
            inserted_ids: List of newly inserted job listing IDs
            updated_ids: List of updated job listing IDs
            company_id: Company ID
            provider_name: Provider name (e.g., 'apollo')
            job_enrichment_id: Job enrichment record ID
            url_to_provider_data: Dict mapping job URL to provider data

        Returns:
            Number of sources created or updated
        """
        if not inserted_ids and not updated_ids:
            return 0

        from bson import ObjectId
        from domains.job_listings.repository import job_listing_repository

        # Fetch all jobs in bulk (avoid N+1 queries)
        all_job_ids = inserted_ids + updated_ids
        job_oids = [ObjectId(job_id) for job_id in all_job_ids]

        # Get all jobs in a single query
        jobs = list(
            job_listing_repository.collection.find(
                {"_id": {"$in": job_oids}}, {"_id": 1, "url": 1}
            )
        )

        # Build lookup map: job_id -> url
        job_id_to_url = {str(job["_id"]): job["url"] for job in jobs}

        # Fetch existing sources once (avoid duplicate query in bulk method)
        existing_docs = list(
            self.collection.find(
                {"job_listing_id": {"$in": job_oids}}, {"job_listing_id": 1}
            )
        )
        existing_ids = {doc["job_listing_id"] for doc in existing_docs}

        # Build sources_data array
        current_time = datetime.now()
        sources_data = []

        job_enrichment_id = (
            str(job_enrichment_id)
            if isinstance(job_enrichment_id, ObjectId)
            else job_enrichment_id
        )

        # Process inserted jobs
        for job_id in inserted_ids:
            url = job_id_to_url.get(job_id)
            if url and url in url_to_provider_data:
                provider_data = url_to_provider_data[url]
                provider_info = ApolloProviderSourceInfo(
                    job_enrichment_id=job_enrichment_id,
                    provider_job_id=provider_data["provider_job_id"],
                    url=provider_data["url"],
                    first_seen_at=current_time,
                    last_seen_at=provider_data.get("last_seen_at") or current_time,
                )
                sources_data.append(
                    {
                        "job_listing_id": job_id,
                        "company_id": company_id,
                        "provider_name": provider_name,
                        "provider_info": provider_info,
                    }
                )

        # Process updated jobs
        for job_id in updated_ids:
            url = job_id_to_url.get(job_id)
            if url and url in url_to_provider_data:
                provider_data = url_to_provider_data[url]
                provider_info = ApolloProviderSourceInfo(
                    job_enrichment_id=job_enrichment_id,
                    provider_job_id=provider_data["provider_job_id"],
                    url=provider_data["url"],
                    first_seen_at=current_time,  # Will be preserved if exists
                    last_seen_at=provider_data.get("last_seen_at") or current_time,
                )
                sources_data.append(
                    {
                        "job_listing_id": job_id,
                        "company_id": company_id,
                        "provider_name": provider_name,
                        "provider_info": provider_info,
                    }
                )

        # Use bulk update method with pre-fetched existing_ids
        if sources_data:
            return self.add_or_update_provider_sources_bulk(sources_data, existing_ids)

        return 0

    def add_or_update_provider_sources_bulk(
        self,
        sources_data: List[Dict[str, any]],
        existing_ids: Optional[set] = None,
    ) -> int:
        """
        Add or update multiple provider sources in bulk
        Much more efficient than calling add_or_update_provider_source multiple times

        Args:
            sources_data: List of dicts with keys:
                - job_listing_id: Job listing ID
                - company_id: Company ID
                - provider_name: Provider name
                - provider_info: ApolloProviderSourceInfo object
            existing_ids: Optional set of existing job_listing_id ObjectIds to avoid duplicate query

        Returns:
            Number of sources created or updated
        """
        if not sources_data:
            return 0

        # Single timestamp for all operations (avoid 1000+ datetime.now() calls)
        current_time = datetime.now()

        # Pre-convert all IDs and cache provider_info dicts (avoid repeated conversions)
        converted_items = []
        for item in sources_data:
            job_listing_oid = (
                ObjectId(item["job_listing_id"])
                if isinstance(item["job_listing_id"], str)
                else item["job_listing_id"]
            )
            company_oid = (
                ObjectId(item["company_id"])
                if isinstance(item["company_id"], str)
                else item["company_id"]
            )
            # Convert provider_info once instead of in loop
            provider_dict = item["provider_info"].model_dump()

            converted_items.append(
                {
                    "job_listing_oid": job_listing_oid,
                    "company_oid": company_oid,
                    "provider_name": item["provider_name"],
                    "provider_dict": provider_dict,
                }
            )

        # Get existing documents (if not provided)
        if existing_ids is None:
            job_listing_oids = [item["job_listing_oid"] for item in converted_items]
            existing_docs = list(
                self.collection.find(
                    {"job_listing_id": {"$in": job_listing_oids}}, {"job_listing_id": 1}
                )
            )
            existing_ids = {doc["job_listing_id"] for doc in existing_docs}

        # Prepare bulk operations (both updates and inserts)
        bulk_operations = []

        for item in converted_items:
            job_listing_oid = item["job_listing_oid"]
            company_oid = item["company_oid"]
            provider_name = item["provider_name"]
            provider_dict = item["provider_dict"]

            if job_listing_oid in existing_ids:
                # Update existing document
                update_data = {
                    f"sources.{provider_name}": provider_dict,
                    "updated_at": current_time,
                }
                bulk_operations.append(
                    UpdateOne(
                        {"job_listing_id": job_listing_oid}, {"$set": update_data}
                    )
                )
            else:
                # Insert new document
                new_doc = {
                    "job_listing_id": job_listing_oid,
                    "company_id": company_oid,
                    "sources": {provider_name: provider_dict},
                    "created_at": current_time,
                    "updated_at": current_time,
                }
                bulk_operations.append(InsertOne(new_doc))

        # Execute single bulk_write with all operations
        if bulk_operations:
            result = self.collection.bulk_write(bulk_operations, ordered=False)
            # Count both inserts and updates
            operations_count = result.inserted_count + result.modified_count
            return operations_count

        return 0

    def remove_provider_source(
        self, job_listing_id: str, provider_name: str
    ) -> Optional[JobListingSourceResponse]:
        """
        Remove a specific provider source from a job listing

        Args:
            job_listing_id: Job listing ID (string representation)
            provider_name: Provider name to remove

        Returns:
            Updated JobListingSourceResponse if successful, None otherwise
        """
        try:
            # Convert to ObjectId for query
            job_listing_oid = (
                ObjectId(job_listing_id)
                if isinstance(job_listing_id, str)
                else job_listing_id
            )
            result = self.collection.update_one(
                {"job_listing_id": job_listing_oid},
                {
                    "$unset": {f"sources.{provider_name}": ""},
                    "$set": {"updated_at": datetime.now()},
                },
            )

            if result.matched_count > 0:
                return self.get_source_by_job_listing_id(job_listing_id)
            return None
        except Exception as e:
            print(f"Error removing provider source: {e}")
            return None

    def get_job_listings_by_provider_job_id(
        self, provider_name: str, provider_job_id: str
    ) -> List[JobListingSourceResponse]:
        """
        Find job listings that have a specific provider job ID

        Args:
            provider_name: Provider name (e.g., 'apollo')
            provider_job_id: Provider's job ID

        Returns:
            List of JobListingSourceResponse objects
        """
        query = {f"sources.{provider_name}.provider_job_id": provider_job_id}
        cursor = self.collection.find(query)

        sources = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            sources.append(JobListingSourceResponse(**doc))
        return sources

    def delete_source(self, job_listing_id: str) -> bool:
        """
        Delete a source tracking document

        Args:
            job_listing_id: Job listing ID (string representation)

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Convert to ObjectId for query
            job_listing_oid = (
                ObjectId(job_listing_id)
                if isinstance(job_listing_id, str)
                else job_listing_id
            )
            result = self.collection.delete_one({"job_listing_id": job_listing_oid})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting source: {e}")
            return False


# Singleton instance
job_listing_source_repository = JobListingSourceRepository()
