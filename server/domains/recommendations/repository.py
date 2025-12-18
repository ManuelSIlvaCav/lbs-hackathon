"""
Repository for recommendation operations
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo import InsertOne, UpdateOne

from .models import (
    RecommendationModel,
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatus,
)
from database import get_collection

logger = logging.getLogger("app")


class RecommendationRepository:
    """Repository for managing recommendation operations"""

    def __init__(self):
        self.collection: Collection = get_collection("recommendations")
        # Create indexes for efficient queries
        self.collection.create_index("candidate_id")
        self.collection.create_index("job_listing_id")
        self.collection.create_index("company_id")
        self.collection.create_index(
            [("candidate_id", 1), ("job_listing_id", 1)], unique=True
        )
        self.collection.create_index("recommendation_status")
        self.collection.create_index("created_at")

    def create_recommendation(
        self, recommendation_data: RecommendationCreate
    ) -> RecommendationResponse:
        """
        Create a single recommendation

        Args:
            recommendation_data: RecommendationCreate object

        Returns:
            RecommendationResponse object with created recommendation data
        """
        # Convert IDs to ObjectId if they're strings
        candidate_oid = (
            ObjectId(recommendation_data.candidate_id)
            if isinstance(recommendation_data.candidate_id, str)
            else recommendation_data.candidate_id
        )
        job_listing_oid = (
            ObjectId(recommendation_data.job_listing_id)
            if isinstance(recommendation_data.job_listing_id, str)
            else recommendation_data.job_listing_id
        )
        company_oid = (
            ObjectId(recommendation_data.company_id)
            if isinstance(recommendation_data.company_id, str)
            else recommendation_data.company_id
        )

        recommendation_model = RecommendationModel(
            candidate_id=candidate_oid,
            job_listing_id=job_listing_oid,
            company_id=company_oid,
            reason=recommendation_data.reason,
            recommendation_status=recommendation_data.recommendation_status,
            created_at=datetime.now(),
        )

        recommendation_dict = recommendation_model.model_dump(
            by_alias=True, exclude=["id"]
        )
        result = self.collection.insert_one(recommendation_dict)

        inserted_recommendation = self.collection.find_one({"_id": result.inserted_id})
        if not inserted_recommendation:
            raise ValueError("Failed to retrieve inserted recommendation")

        inserted_recommendation["_id"] = str(inserted_recommendation["_id"])
        return RecommendationResponse(**inserted_recommendation)

    def create_recommendations_bulk(
        self, recommendations_data: List[RecommendationCreate]
    ) -> tuple[List[str], int]:
        """
        Create multiple recommendations in bulk

        Args:
            recommendations_data: List of RecommendationCreate objects

        Returns:
            Tuple of (list of inserted IDs, count of skipped duplicates)
        """
        if not recommendations_data:
            return [], 0

        current_time = datetime.now()
        bulk_operations = []
        inserted_ids = []

        for rec_data in recommendations_data:
            # Convert IDs to ObjectId
            candidate_oid = (
                ObjectId(rec_data.candidate_id)
                if isinstance(rec_data.candidate_id, str)
                else rec_data.candidate_id
            )
            job_listing_oid = (
                ObjectId(rec_data.job_listing_id)
                if isinstance(rec_data.job_listing_id, str)
                else rec_data.job_listing_id
            )
            company_oid = (
                ObjectId(rec_data.company_id)
                if isinstance(rec_data.company_id, str)
                else rec_data.company_id
            )

            # Pre-generate ObjectId to track inserted IDs
            new_id = ObjectId()
            inserted_ids.append(str(new_id))

            # Build document dict directly
            rec_doc = {
                "_id": new_id,
                "candidate_id": candidate_oid,
                "job_listing_id": job_listing_oid,
                "company_id": company_oid,
                "reason": rec_data.reason,
                "recommendation_status": (
                    rec_data.recommendation_status.value
                    if isinstance(rec_data.recommendation_status, RecommendationStatus)
                    else rec_data.recommendation_status
                ),
                "created_at": current_time,
                "recommended_at": None,
                "deleted_at": None,
            }

            bulk_operations.append(InsertOne(rec_doc))

        # Execute bulk insert
        if bulk_operations:
            try:
                result = self.collection.bulk_write(bulk_operations, ordered=False)
                actual_inserted = result.inserted_count
                skipped = len(bulk_operations) - actual_inserted

                logger.info(
                    f"Bulk insert recommendations: {actual_inserted} inserted, {skipped} skipped (duplicates)"
                )

                # Return only IDs that were actually inserted
                if skipped > 0:
                    # Query to get which ones were actually inserted
                    inserted_oids = [ObjectId(id_str) for id_str in inserted_ids]
                    existing = self.collection.find(
                        {"_id": {"$in": inserted_oids}}, {"_id": 1}
                    )
                    actual_inserted_ids = [str(doc["_id"]) for doc in existing]
                    return actual_inserted_ids, skipped

                return inserted_ids, 0

            except Exception as e:
                # Handle duplicate key errors
                logger.warning(f"Bulk insert had errors: {str(e)}")
                # Query to find which ones were inserted
                inserted_oids = [ObjectId(id_str) for id_str in inserted_ids]
                existing = self.collection.find(
                    {"_id": {"$in": inserted_oids}}, {"_id": 1}
                )
                actual_inserted_ids = [str(doc["_id"]) for doc in existing]
                skipped = len(inserted_ids) - len(actual_inserted_ids)
                return actual_inserted_ids, skipped

        return [], 0

    def get_recommendation(
        self, recommendation_id: str
    ) -> Optional[RecommendationResponse]:
        """
        Get a single recommendation by ID

        Args:
            recommendation_id: Recommendation ID (string representation)

        Returns:
            RecommendationResponse if found, None otherwise
        """
        try:
            recommendation_oid = (
                ObjectId(recommendation_id)
                if isinstance(recommendation_id, str)
                else recommendation_id
            )
            recommendation = self.collection.find_one({"_id": recommendation_oid})

            if recommendation:
                recommendation["_id"] = str(recommendation["_id"])
                return RecommendationResponse(**recommendation)
            return None

        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return None

    def get_recommendations(
        self,
        candidate_id: Optional[str] = None,
        job_listing_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[RecommendationStatus] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[RecommendationResponse]:
        """
        Get recommendations with optional filters

        Args:
            candidate_id: Filter by candidate ID
            job_listing_id: Filter by job listing ID
            company_id: Filter by company ID
            status: Filter by recommendation status
            limit: Maximum number of results
            skip: Number of results to skip (pagination)

        Returns:
            List of RecommendationResponse objects
        """
        query = {}

        if candidate_id:
            candidate_oid = (
                ObjectId(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            query["candidate_id"] = candidate_oid

        if job_listing_id:
            job_listing_oid = (
                ObjectId(job_listing_id)
                if isinstance(job_listing_id, str)
                else job_listing_id
            )
            query["job_listing_id"] = job_listing_oid

        if company_id:
            company_oid = (
                ObjectId(company_id) if isinstance(company_id, str) else company_id
            )
            query["company_id"] = company_oid

        if status:
            query["recommendation_status"] = (
                status.value if isinstance(status, RecommendationStatus) else status
            )

        # Exclude soft-deleted recommendations by default
        query["deleted_at"] = None

        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )

        recommendations = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            recommendations.append(RecommendationResponse(**doc))

        return recommendations

    def update_recommendation_status(
        self, recommendation_id: str, status: RecommendationStatus
    ) -> Optional[RecommendationResponse]:
        """
        Update recommendation status

        Args:
            recommendation_id: Recommendation ID
            status: New status

        Returns:
            Updated RecommendationResponse if successful, None otherwise
        """
        try:
            recommendation_oid = (
                ObjectId(recommendation_id)
                if isinstance(recommendation_id, str)
                else recommendation_id
            )

            update_data = {
                "recommendation_status": (
                    status.value if isinstance(status, RecommendationStatus) else status
                )
            }

            # Set recommended_at when status changes to RECOMMENDED
            if status == RecommendationStatus.RECOMMENDED:
                update_data["recommended_at"] = datetime.now()

            result = self.collection.update_one(
                {"_id": recommendation_oid}, {"$set": update_data}
            )

            if result.modified_count > 0:
                return self.get_recommendation(recommendation_id)
            return None

        except Exception as e:
            logger.error(f"Error updating recommendation status: {e}")
            return None

    def soft_delete_recommendation(
        self, recommendation_id: str
    ) -> Optional[RecommendationResponse]:
        """
        Soft delete a recommendation

        Args:
            recommendation_id: Recommendation ID

        Returns:
            Updated RecommendationResponse if successful, None otherwise
        """
        try:
            recommendation_oid = (
                ObjectId(recommendation_id)
                if isinstance(recommendation_id, str)
                else recommendation_id
            )

            result = self.collection.update_one(
                {"_id": recommendation_oid},
                {
                    "$set": {
                        "deleted_at": datetime.now(),
                        "recommendation_status": RecommendationStatus.DELETED.value,
                    }
                },
            )

            if result.modified_count > 0:
                return self.get_recommendation(recommendation_id)
            return None

        except Exception as e:
            logger.error(f"Error soft deleting recommendation: {e}")
            return None

    def delete_recommendation(self, recommendation_id: str) -> bool:
        """
        Permanently delete a recommendation

        Args:
            recommendation_id: Recommendation ID

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            recommendation_oid = (
                ObjectId(recommendation_id)
                if isinstance(recommendation_id, str)
                else recommendation_id
            )
            result = self.collection.delete_one({"_id": recommendation_oid})
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting recommendation: {e}")
            return False

    def get_recommendations_with_details(
        self,
        candidate_id: Optional[str] = None,
        job_listing_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[RecommendationStatus] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> Dict:
        """
        Get recommendations with full job listing and company details using aggregation

        Args:
            candidate_id: Filter by candidate ID
            job_listing_id: Filter by job listing ID
            company_id: Filter by company ID
            status: Filter by recommendation status
            limit: Maximum number of results
            skip: Number of results to skip (pagination)

        Returns:
            Dict with paginated recommendations including job and company details
        """
        # Build match query
        match_query = {"deleted_at": None}

        if candidate_id:
            try:
                candidate_oid = (
                    ObjectId(candidate_id)
                    if isinstance(candidate_id, str)
                    else candidate_id
                )
                match_query["candidate_id"] = candidate_oid
            except Exception as e:
                logger.error(f"Invalid candidate_id: {candidate_id} - {e}")
                # Return empty result for invalid ObjectId
                return {
                    "items": [],
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "has_more": False,
                }

        if job_listing_id:
            try:
                job_listing_oid = (
                    ObjectId(job_listing_id)
                    if isinstance(job_listing_id, str)
                    else job_listing_id
                )
                match_query["job_listing_id"] = job_listing_oid
            except Exception as e:
                logger.error(f"Invalid job_listing_id: {job_listing_id} - {e}")
                return {
                    "items": [],
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "has_more": False,
                }

        if company_id:
            try:
                company_oid = (
                    ObjectId(company_id) if isinstance(company_id, str) else company_id
                )
                match_query["company_id"] = company_oid
            except Exception as e:
                logger.error(f"Invalid company_id: {company_id} - {e}")
                return {
                    "items": [],
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "has_more": False,
                }

        if status:
            match_query["recommendation_status"] = (
                status.value if isinstance(status, RecommendationStatus) else status
            )

        # Build aggregation pipeline
        pipeline = [
            {"$match": match_query},
            {"$sort": {"created_at": -1}},
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        {"$skip": skip},
                        {"$limit": limit},
                        # Lookup job listing
                        {
                            "$lookup": {
                                "from": "job_listings",
                                "localField": "job_listing_id",
                                "foreignField": "_id",
                                "as": "job_listing",
                            }
                        },
                        {
                            "$unwind": {
                                "path": "$job_listing",
                                "preserveNullAndEmptyArrays": True,
                            }
                        },
                        # Lookup company
                        {
                            "$lookup": {
                                "from": "companies",
                                "localField": "company_id",
                                "foreignField": "_id",
                                "as": "company",
                            }
                        },
                        {
                            "$unwind": {
                                "path": "$company",
                                "preserveNullAndEmptyArrays": True,
                            }
                        },
                        # Convert ObjectIds to strings for response
                        {
                            "$addFields": {
                                "_id": {"$toString": "$_id"},
                                "candidate_id": {"$toString": "$candidate_id"},
                                "job_listing_id": {"$toString": "$job_listing_id"},
                                "company_id": {"$toString": "$company_id"},
                                "job_listing._id": {"$toString": "$job_listing._id"},
                                "job_listing.company_id": {
                                    "$toString": "$job_listing.company_id"
                                },
                                "company._id": {"$toString": "$company._id"},
                            }
                        },
                    ],
                }
            },
        ]

        try:
            result = list(self.collection.aggregate(pipeline))

            if not result:
                return {
                    "items": [],
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "has_more": False,
                }

            metadata = result[0]["metadata"]
            total = metadata[0]["total"] if metadata else 0
            items = result[0]["data"]

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total,
            }

        except Exception as e:
            logger.error(f"Error getting recommendations with details: {e}")
            raise


# Singleton instance
recommendation_repository = RecommendationRepository()
