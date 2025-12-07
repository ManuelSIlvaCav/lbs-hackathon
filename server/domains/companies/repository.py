"""
Company repository for database operations
"""

from typing import List, Optional
from pymongo.collection import Collection
from bson import ObjectId

from database import get_collection
from .models import CompanyModel, CompanyResponse, CompanyCreate
from datetime import datetime


class CompanyRepository:
    """Repository for company operations"""

    def __init__(self):
        self.collection: Collection = get_collection("companies")
        # Create text index for search functionality
        self.collection.create_index([("name", "text"), ("description", "text")])

    def search_companies(
        self, query: str = "", skip: int = 0, limit: int = 20
    ) -> tuple[List[CompanyResponse], int]:
        """
        Search companies by text query with pagination

        Args:
            query: Search text (searches in name and description)
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            Tuple of (list of companies, total count)
        """
        if query:
            # Text search
            filter_query = {"$text": {"$search": query}}
            # Sort by text score
            cursor = (
                self.collection.find(filter_query)
                .sort([("score", {"$meta": "textScore"})])
                .skip(skip)
                .limit(limit)
            )
        else:
            # No query, return all companies sorted by name
            filter_query = {}
            cursor = (
                self.collection.find(filter_query)
                .sort("name", 1)
                .skip(skip)
                .limit(limit)
            )

        companies = []
        for doc in cursor:
            companies.append(
                CompanyResponse(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    company_url=doc.get("company_url"),
                    industry=doc.get("industry"),
                    description=doc.get("description"),
                    logo_url=doc.get("logo_url"),
                )
            )

        # Get total count
        total_count = self.collection.count_documents(filter_query)

        return companies, total_count

    def get_company_by_id(self, company_id: str) -> Optional[CompanyResponse]:
        """Get a company by ID"""
        doc = self.collection.find_one({"_id": ObjectId(company_id)})
        if not doc:
            return None

        return CompanyResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            company_url=doc.get("company_url"),
            industry=doc.get("industry"),
            description=doc.get("description"),
            logo_url=doc.get("logo_url"),
        )

    def create_company(self, company_data) -> CompanyResponse:
        """Create a new company"""
        now = datetime.utcnow()

        # Handle both dict and CompanyCreate object
        if isinstance(company_data, dict):
            company_dict = company_data.copy()
        else:
            company_dict = company_data.model_dump()

        company_dict["created_at"] = now
        company_dict["updated_at"] = now

        result = self.collection.insert_one(company_dict)

        return CompanyResponse(
            id=str(result.inserted_id),
            name=company_dict["name"],
            company_url=company_dict.get("company_url"),
            industry=company_dict.get("industry"),
            description=company_dict.get("description"),
            logo_url=company_dict.get("logo_url"),
        )


# Singleton instance
company_repository = CompanyRepository()
