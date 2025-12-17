"""
Data Processor Repository for enrichment data operations
Handles company_enrichments and company_job_enrichments collections
"""

from typing import Optional
from pymongo.collection import Collection
from datetime import datetime

from database import get_collection
from .enrichment_models import (
    CompanyEnrichmentCreate,
    CompanyEnrichmentResponse,
    CompanyJobEnrichmentCreate,
    CompanyJobEnrichmentResponse,
)


class DataProcessorRepository:
    """Repository for enrichment data operations"""

    def __init__(self):
        self.enrichments_collection: Collection = get_collection("company_enrichments")
        self.job_enrichments_collection: Collection = get_collection(
            "company_job_enrichments"
        )
        # Create indexes for enrichments
        self.enrichments_collection.create_index("company_id")
        self.enrichments_collection.create_index("provider")
        self.enrichments_collection.create_index("enriched_at")
        # Create indexes for job enrichments
        self.job_enrichments_collection.create_index("company_id")
        self.job_enrichments_collection.create_index("provider")
        self.job_enrichments_collection.create_index("enriched_at")

    def save_enrichment(
        self, enrichment_data: CompanyEnrichmentCreate
    ) -> CompanyEnrichmentResponse:
        """Save enrichment data for a company"""
        now = datetime.now()

        enrichment_dict = enrichment_data.model_dump()
        enrichment_dict["enriched_at"] = now

        result = self.enrichments_collection.insert_one(enrichment_dict)

        return CompanyEnrichmentResponse(
            id=str(result.inserted_id),
            company_id=enrichment_data.company_id,
            provider=enrichment_data.provider,
            enriched_at=now,
        )

    def get_latest_enrichment(
        self, company_id: str, provider: str = "apollo"
    ) -> Optional[dict]:
        """Get the latest enrichment data for a company"""
        doc = self.enrichments_collection.find_one(
            {"company_id": company_id, "provider": provider},
            sort=[("enriched_at", -1)],
        )
        return doc

    def save_job_enrichment(
        self, enrichment_data: CompanyJobEnrichmentCreate
    ) -> CompanyJobEnrichmentResponse:
        """Save job enrichment data for a company"""

        enrichment_dict = enrichment_data.model_dump()

        result = self.job_enrichments_collection.insert_one(enrichment_dict)

        return CompanyJobEnrichmentResponse(
            id=str(result.inserted_id),
            company_id=enrichment_data.company_id,
            provider=enrichment_data.provider,
            job_count=enrichment_data.job_count,
        )

    def get_latest_job_enrichment(
        self, company_id: str, provider: str = "apollo"
    ) -> Optional[dict]:
        """Get the latest job enrichment data for a company"""
        doc = self.job_enrichments_collection.find_one(
            {"company_id": company_id, "provider": provider},
            sort=[("enriched_at", -1), ("updated_at", -1)],
        )
        return doc

    def get_all_job_enrichments(self):
        """Get all job enrichments sorted by enriched_at"""
        return self.job_enrichments_collection.find().sort("enriched_at", 1)


# Singleton instance
data_processor_repository = DataProcessorRepository()
