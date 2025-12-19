"""
Repository for search options operations
"""

import logging
from typing import Optional
from datetime import datetime
from pymongo.collection import Collection

from .models import SearchOptionsModel, SearchOptionsResponse
from database import get_collection

logger = logging.getLogger("app")


class SearchOptionsRepository:
    """Repository for managing search options"""

    def __init__(self):
        self.collection: Collection = get_collection("search_options")
        self.collection.create_index([("updated_at", -1)])

    def get_search_options(self) -> Optional[SearchOptionsResponse]:
        """
        Get the current search options

        Returns:
            SearchOptionsResponse if found, None otherwise
        """
        try:
            # Get the most recent search options document
            doc = self.collection.find_one(sort=[("updated_at", -1)])

            if doc:
                doc["_id"] = str(doc["_id"])

                # Handle backward compatibility: convert old format to new format
                if doc.get("countries") and isinstance(doc["countries"], list):
                    # Check if countries is in old format (list of dicts)
                    if doc["countries"] and isinstance(doc["countries"][0], dict):
                        # Convert old format: [{"country": "USA", "cities": [...]}]
                        # to new format: ["USA", ...]
                        doc["countries"] = [c["country"] for c in doc["countries"]]
                        logger.info(
                            "Converted countries from old format to new format",
                            extra={"context": "SearchOptionsRepository"},
                        )

                options = SearchOptionsModel(**doc)
                return SearchOptionsResponse(
                    countries=options.countries,
                    profile_categories=options.profile_categories,
                    role_titles=options.role_titles,
                    updated_at=options.updated_at,
                )

            return None

        except Exception as e:
            logger.error(
                "Error getting search options",
                extra={"context": "SearchOptionsRepository", "error_msg": str(e)},
            )
            return None

    def update_search_options(
        self,
        countries: list[str],
        profile_categories: list[str],
        role_titles: list[str],
    ) -> SearchOptionsResponse:
        """
        Update search options (creates new document, old ones kept for history)

        Args:
            countries: List of country names
            profile_categories: List of profile categories
            role_titles: List of role titles

        Returns:
            SearchOptionsResponse with updated data
        """
        try:
            # Create new search options document
            search_options = SearchOptionsModel(
                countries=countries,
                profile_categories=profile_categories,
                role_titles=role_titles,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Insert into database
            doc = search_options.model_dump(by_alias=True, exclude=["id"])
            result = self.collection.insert_one(doc)

            logger.info(
                "Search options updated",
                extra={
                    "context": "SearchOptionsRepository",
                    "document_id": str(result.inserted_id),
                    "countries_count": len(countries),
                    "categories_count": len(profile_categories),
                    "roles_count": len(role_titles),
                },
            )

            return SearchOptionsResponse(
                countries=countries,
                profile_categories=profile_categories,
                role_titles=role_titles,
                updated_at=datetime.now(),
            )

        except Exception as e:
            logger.error(
                "Error updating search options",
                extra={"context": "SearchOptionsRepository", "error_msg": str(e)},
            )
            raise


# Singleton instance
search_options_repository = SearchOptionsRepository()
