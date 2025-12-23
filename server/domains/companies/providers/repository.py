"""
Repository for company search results
"""

from typing import List, Optional
from pymongo.collection import Collection
from datetime import datetime

from database import get_collection
from .models import (
    CompanySearchResultCreate,
    CompanySearchResultResponse,
)


class CompanySearchRepository:
    """Repository for company search operations"""

    def __init__(self):
        self.collection: Collection = get_collection("company_search_results")
        # Create indexes for efficient querying
        self.collection.create_index("provider")

    def save_search_result(
        self, result_data: CompanySearchResultCreate
    ) -> CompanySearchResultResponse:
        """
        Save a search result from a provider
        If a result with the same provider exists, update it
        """
        now = datetime.now()

        # Check if result already exists
        existing = self.collection.find_one({"provider": result_data.provider})

        if existing:
            # Update existing record
            self.collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "search_query": result_data.search_query,
                        "raw_data": result_data.raw_data,
                        "last_synced_at": now,
                    }
                },
            )
            result_id = str(existing["_id"])
            created_at = existing["created_at"]
        else:
            # Create new record
            result_dict = result_data.model_dump()
            result_dict["created_at"] = now
            result_dict["last_synced_at"] = now

            result = self.collection.insert_one(result_dict)
            result_id = str(result.inserted_id)
            created_at = now

        return CompanySearchResultResponse(
            id=result_id,
            provider=result_data.provider,
            search_query=result_data.search_query,
            created_at=created_at,
            last_synced_at=now,
        )

    def get_by_provider(self, provider: str) -> Optional[CompanySearchResultResponse]:
        """Get a search result by provider"""
        doc = self.collection.find_one({"provider": provider})
        if not doc:
            return None

        return CompanySearchResultResponse(
            id=str(doc["_id"]),
            provider=doc["provider"],
            search_query=doc["search_query"],
            created_at=doc["created_at"],
            last_synced_at=doc["last_synced_at"],
        )

    def get_all_by_provider(self, provider: str) -> List[CompanySearchResultResponse]:
        """Get all search results from a specific provider"""
        cursor = self.collection.find({"provider": provider})
        results = []

        for doc in cursor:
            results.append(
                CompanySearchResultResponse(
                    id=str(doc["_id"]),
                    provider=doc["provider"],
                    search_query=doc["search_query"],
                    created_at=doc["created_at"],
                    last_synced_at=doc["last_synced_at"],
                )
            )

        return results


# Singleton instance
company_search_repository = CompanySearchRepository()
