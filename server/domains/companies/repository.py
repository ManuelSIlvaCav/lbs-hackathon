"""
Company repository for database operations
"""

import logging
from typing import List, Optional
from pymongo.collection import Collection
from bson import ObjectId

from database import get_collection
from utils.singleton_class import SingletonMeta
from .models import CompanyModel
from datetime import datetime


logger = logging.getLogger("app")


class CompanyRepository(metaclass=SingletonMeta):
    """Repository for company operations"""

    def __init__(self):
        self.collection: Collection = get_collection("companies")
        try:
            # Create text index for search functionality
            self.collection.create_index([("name", "text"), ("description", "text")])
        except Exception as e:
            logger.error(
                "Failed to create text index on companies collection",
                extra={"context": "CompanyRepository.__init__", "error_msg": str(e)},
            )
            pass

    def search_companies(
        self, query: str = "", skip: int = 0, limit: int = 20
    ) -> tuple[List[CompanyModel], int]:
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
                CompanyModel(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    company_url=doc.get("company_url"),
                    industries=doc.get("industries"),
                    description=doc.get("description"),
                    logo_url=doc.get("logo_url"),
                )
            )

        # Get total count
        total_count = self.collection.count_documents(filter_query)

        return companies, total_count

    def get_company_by_id(self, company_id: str) -> Optional[CompanyModel]:
        """Get a company by ID"""
        doc = self.collection.find_one({"_id": ObjectId(company_id)})
        if not doc:
            return None

        return CompanyModel(
            id=str(doc["_id"]),
            name=doc["name"],
            company_url=doc.get("company_url"),
            industries=doc.get("industries"),
            description=doc.get("description"),
            logo_url=doc.get("logo_url"),
        )

    def create_company(self, company_data) -> CompanyModel:
        """Create a new company"""
        now = datetime.now()

        # Handle both dict and CompanyCreate object
        if isinstance(company_data, dict):
            company_dict = company_data.copy()
        else:
            company_dict = company_data.model_dump()

        company_dict["created_at"] = now
        company_dict["updated_at"] = now

        result = self.collection.insert_one(company_dict)

        return CompanyModel(
            id=str(result.inserted_id),
            name=company_dict["name"],
            company_url=company_dict.get("company_url"),
            industries=company_dict.get("industries"),
            description=company_dict.get("description"),
            logo_url=company_dict.get("logo_url"),
        )

    def update_company_from_enrichment(
        self, company_id: str, enriched_data: dict
    ) -> Optional[CompanyModel]:
        """Update company fields from enrichment data"""
        org = enriched_data.get("organization", {})

        # Build description from various fields
        description = ""

        if org.get("short_description"):
            description += org.get("short_description") + ". "

        # Prepare update data
        update_data = {
            "updated_at": datetime.now(),
        }

        # Add optional fields if they exist
        if description:
            update_data["description"] = description

        if org.get("industries"):
            update_data["industries"] = org["industries"]

        if org.get("logo_url"):
            update_data["logo_url"] = org["logo_url"]

        if org.get("linkedin_url"):
            update_data["linkedin_url"] = org["linkedin_url"]

        # Update the company
        result = self.collection.find_one_and_update(
            {"_id": ObjectId(company_id)},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            return None

        return CompanyModel(
            id=str(result["_id"]),
            name=result["name"],
            company_url=result.get("company_url"),
            industries=result.get("industries"),
            description=result.get("description"),
            logo_url=result.get("logo_url"),
            linkedin_url=result.get("linkedin_url"),
            domain=result.get("domain"),
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at"),
        )

    def get_followed_company_ids(self) -> list:
        """
        Get all company IDs that are followed by at least one candidate.

        Returns:
            List[ObjectId]: List of company ObjectIds that have at least one follower
        """
        from domains.candidates.repository import candidate_repository

        # Get all companies that are followed by at least one candidate
        followed_companies = candidate_repository.collection.aggregate(
            [
                # Unwind the followed_companies array
                {"$unwind": "$followed_companies"},
                # Group by company_id to get unique companies
                {
                    "$group": {
                        "_id": "$followed_companies.company_id",
                        "follower_count": {"$sum": 1},
                    }
                },
                # Sort by follower count descending
                {"$sort": {"follower_count": -1}},
            ]
        )

        return [doc["_id"] for doc in followed_companies]

    def get_all_companies(self) -> List[CompanyModel]:
        """Get all companies from the database"""
        cursor = self.collection.find({})

        companies = []
        for doc in cursor:
            companies.append(
                CompanyModel(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    company_url=doc.get("company_url"),
                    industries=doc.get("industries"),
                    description=doc.get("description"),
                    logo_url=doc.get("logo_url"),
                    linkedin_url=doc.get("linkedin_url"),
                    domain=doc.get("domain"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    last_enriched_at=doc.get("last_enriched_at"),
                )
            )

        return companies

    def get_all_companies_to_enrich(self) -> List[CompanyModel]:
        """Get all companies that need enrichment (not enriched in last 24 hours)"""
        from datetime import timedelta

        # Calculate timestamp for 24 hours ago
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        # Find companies where last_enriched_at is null or older than 24 hours
        cursor = self.collection.find(
            {
                "$or": [
                    {"last_enriched_at": None},
                    {"last_enriched_at": {"$exists": False}},
                    {"last_enriched_at": {"$lt": twenty_four_hours_ago}},
                ]
            }
        )

        companies = []
        for doc in cursor:
            companies.append(
                CompanyModel(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    company_url=doc.get("company_url"),
                    industries=doc.get("industries"),
                    description=doc.get("description"),
                    logo_url=doc.get("logo_url"),
                    linkedin_url=doc.get("linkedin_url"),
                    domain=doc.get("domain"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    last_enriched_at=doc.get("last_enriched_at"),
                )
            )

        logger.info(
            f"Found {len(companies)} companies to enrich (not enriched in last 24 hours)",
            extra={
                "context": "get_all_companies_to_enrich",
                "company_count": len(companies),
            },
        )

        return companies

    def update_company_enrichment_timestamp(self, company_id: str) -> bool:
        """Update the last_enriched_at timestamp for a company"""
        try:
            now = datetime.now()
            result = self.collection.update_one(
                {"_id": ObjectId(company_id)},
                {
                    "$set": {
                        "last_enriched_at": now,
                        "updated_at": now,
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(
                f"Failed to update enrichment timestamp for company {company_id}",
                extra={
                    "context": "update_company_enrichment_timestamp",
                    "company_id": company_id,
                    "error_msg": str(e),
                },
            )
            return False


# Singleton instance
company_repository = CompanyRepository()
