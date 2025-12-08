"""
Repository for job listing source operations
Tracks job listings across multiple providers/sources
"""

from typing import List, Optional, Dict
from datetime import datetime
from pymongo.collection import Collection
from pymongo import UpdateOne

from .source_models import (
    JobListingSourceModel,
    JobListingSourceCreate,
    JobListingSourceResponse,
    ProviderSourceInfo,
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
        source_model = JobListingSourceModel(
            job_listing_id=source_data.job_listing_id,
            company_id=source_data.company_id,
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
            job_listing_id: Job listing ID to look up

        Returns:
            JobListingSourceResponse if found, None otherwise
        """
        try:
            source = self.collection.find_one({"job_listing_id": job_listing_id})
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
            company_id: Company ID to filter by

        Returns:
            List of JobListingSourceResponse objects
        """
        cursor = self.collection.find({"company_id": company_id})
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
        provider_info: ProviderSourceInfo,
    ) -> JobListingSourceResponse:
        """
        Add or update a provider source for a job listing
        Creates the source document if it doesn't exist

        Args:
            job_listing_id: Job listing ID
            company_id: Company ID
            provider_name: Name of the provider (e.g., 'apollo', 'linkedin')
            provider_info: Provider source information

        Returns:
            Updated JobListingSourceResponse
        """
        # Try to find existing source document
        existing = self.collection.find_one({"job_listing_id": job_listing_id})

        if existing:
            # Update existing document
            update_data = {
                f"sources.{provider_name}": provider_info.model_dump(),
                "updated_at": datetime.now(),
            }
            self.collection.update_one(
                {"job_listing_id": job_listing_id}, {"$set": update_data}
            )
        else:
            # Create new document
            source_data = JobListingSourceCreate(
                job_listing_id=job_listing_id,
                company_id=company_id,
                sources={provider_name: provider_info},
            )
            return self.create_source(source_data)

        # Return updated document
        result = self.get_source_by_job_listing_id(job_listing_id)
        if not result:
            raise ValueError("Failed to retrieve updated source")
        return result

    def add_or_update_provider_sources_bulk(
        self,
        sources_data: List[Dict[str, any]],
    ) -> int:
        """
        Add or update multiple provider sources in bulk
        Much more efficient than calling add_or_update_provider_source multiple times

        Args:
            sources_data: List of dicts with keys:
                - job_listing_id: Job listing ID
                - company_id: Company ID
                - provider_name: Provider name
                - provider_info: ProviderSourceInfo object

        Returns:
            Number of sources created or updated
        """
        if not sources_data:
            return 0

        # Get all existing job_listing_ids
        job_listing_ids = [item["job_listing_id"] for item in sources_data]
        existing_docs = list(
            self.collection.find(
                {"job_listing_id": {"$in": job_listing_ids}}, {"job_listing_id": 1}
            )
        )
        existing_ids = {doc["job_listing_id"] for doc in existing_docs}

        # Prepare bulk operations
        bulk_operations = []
        new_documents = []

        for item in sources_data:
            job_listing_id = item["job_listing_id"]
            company_id = item["company_id"]
            provider_name = item["provider_name"]
            provider_info = item["provider_info"]

            if job_listing_id in existing_ids:
                # Update existing document
                update_data = {
                    f"sources.{provider_name}": provider_info.model_dump(),
                    "updated_at": datetime.now(),
                }
                bulk_operations.append(
                    UpdateOne({"job_listing_id": job_listing_id}, {"$set": update_data})
                )
            else:
                # Prepare new document
                source_model = JobListingSourceModel(
                    job_listing_id=job_listing_id,
                    company_id=company_id,
                    sources={provider_name: provider_info},
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                new_documents.append(
                    source_model.model_dump(by_alias=True, exclude=["id"])
                )

        # Execute bulk operations
        operations_count = 0

        if bulk_operations:
            result = self.collection.bulk_write(bulk_operations, ordered=False)
            operations_count += result.modified_count

        if new_documents:
            result = self.collection.insert_many(new_documents, ordered=False)
            operations_count += len(result.inserted_ids)

        return operations_count

    def remove_provider_source(
        self, job_listing_id: str, provider_name: str
    ) -> Optional[JobListingSourceResponse]:
        """
        Remove a specific provider source from a job listing

        Args:
            job_listing_id: Job listing ID
            provider_name: Provider name to remove

        Returns:
            Updated JobListingSourceResponse if successful, None otherwise
        """
        try:
            result = self.collection.update_one(
                {"job_listing_id": job_listing_id},
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
            job_listing_id: Job listing ID

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"job_listing_id": job_listing_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting source: {e}")
            return False


# Singleton instance
job_listing_source_repository = JobListingSourceRepository()
