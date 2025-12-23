from bson import ObjectId
from domains.companies.repository import company_repository
from domains.job_listings.repository import job_listing_repository
from domains.companies.data_processor_repository import data_processor_repository
from utils.singleton_class import SingletonMeta


class CompanyService(metaclass=SingletonMeta):
    def __init__(
        self, company_repository, job_listing_repository, data_processor_repository
    ):

        self.company_repository = company_repository
        self.job_listing_repository = job_listing_repository
        self.data_processor_repository = data_processor_repository

    def get_job_listings(self, company_id: str, source_status: str) -> list[str]:
        """
        Enrich job listings for a given company.

        Args:
            company_id (str): The ID of the company to enrich job listings for.
        Returns:
            List of job listing IDs matching the criteria.List[str
        """
        # Get job listings with specified source_status
        # Build query based on source_status parameter
        if source_status == "scrapped":
            # For initial enrichment: get jobs with null or 'scrapped' status
            status_query = {
                "$or": [{"source_status": None}, {"source_status": "scrapped"}]
            }
        else:
            # For re-validation/revision: get jobs with specific status (e.g., 'enriched')
            status_query = {"source_status": source_status}

        job_listings = self.job_listing_repository.collection.find(
            {
                "company_id": ObjectId(company_id),
                **status_query,
            }
        ).sort("updated_at", -1)

        job_listing_ids = [str(job["_id"]) for job in job_listings]
        return job_listing_ids


# Singleton instance
company_service = CompanyService(
    job_listing_repository=job_listing_repository,
    company_repository=company_repository,
    data_processor_repository=data_processor_repository,
)
