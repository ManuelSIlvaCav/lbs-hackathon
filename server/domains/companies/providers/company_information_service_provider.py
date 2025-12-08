from typing import Any, Dict, List
import logging
from datetime import datetime

from domains.job_listings.source_models import ProviderSourceInfo
from domains.job_listings.source_repository import job_listing_source_repository

from .base import CompanyInformationServiceProvider

from ..enrichment_models import CompanyEnrichmentCreate, CompanyJobEnrichmentCreate
from ..models import CompanyModel
from domains.job_listings.models import JobListingResponse, JobListingCreate
from ..repository import company_repository
from domains.job_listings.repository import job_listing_repository
from ..data_processor_repository import data_processor_repository

logger = logging.getLogger("app")


class InformationServiceContext:
    """
    The basic Context class, which is configured with a concrete implementation of a provider
    """

    def __init__(self, provider: CompanyInformationServiceProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> CompanyInformationServiceProvider:
        return self._provider

    @provider.setter
    def provider(self, provider: CompanyInformationServiceProvider) -> None:
        self._provider = provider

    def get_company_information(self, domain: str) -> None:
        result = self._provider.get_company_information(domain)
        return result

    def search_companies(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search for companies by name or other criteria

        Args:
            query: Search query (company name, domain, etc.)
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing search results in provider's format
        """
        result = self._provider.search_companies(query, **kwargs)
        return result

    def search_and_save(
        self, query: str, page: int = 1, per_page: int = 100, **kwargs
    ) -> tuple[list[CompanyModel], Dict[str, Any]]:
        """
        Search for companies and save results to repository

        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            **kwargs: Additional provider-specific parameters

        Returns:
            tuple: A tuple containing:
                - A list of CompanyModel objects
                - A dictionary with additional response metadata
        """
        result = self._provider.search_and_save(
            query=query, page=page, per_page=per_page, **kwargs
        )
        return result

    def enrich_and_save(self, company_id: str, domain: str, **kwargs) -> CompanyModel:
        """
        Enrich a company using provider's API and save enrichment data

        Args:
            company_id: The ID of the company to enrich
            domain: Company domain to use for enrichment lookup
            **kwargs: Additional provider-specific parameters

        Returns:
            tuple: A tuple containing:
                - A CompanyModel object with the updated company data
                - A dictionary with the raw enrichment response
        """

        response = self.get_company_information(domain)

        # Validate response has organization data
        if "organization" not in response:
            raise Exception(
                "Invalid response from Apollo.io - missing organization data"
            )

        # Save enrichment data to data processor repository
        try:
            enrichment_record = CompanyEnrichmentCreate(
                company_id=company_id,
                provider=self._provider.provider_name,
                raw_data=response,
            )
            data_processor_repository.save_enrichment(enrichment_record)
            logger.info(f"Saved enrichment data for company {company_id}")
        except Exception as e:
            logger.error(f"Failed to save enrichment data: {str(e)}")
            # Continue even if save fails

        # Update company with enriched data
        updated_company = company_repository.update_company_from_enrichment(
            company_id, response
        )

        if not updated_company:
            raise ValueError("Failed to update company with enriched data")

        logger.info(f"Successfully enriched company {company_id}")

        return updated_company

    def get_job_listings(
        self, company_id: str, organization_id: str
    ) -> List[JobListingResponse]:
        """
        Get job listings for a company from the provider and save results

        Args:
            company_id: Internal company ID for saving results
            organization_id: Provider-specific organization/company ID

        Returns:
            List of JobListingResponse objects in our standard format
        """
        # Get raw response from provider
        raw_response = self._provider.get_job_listings(organization_id)

        # Map provider response to our standard JobListing format
        job_listings = self._map_job_listings_to_standard(raw_response)

        # Save job enrichment metadata to data processor repository
        job_enrichment_id = None
        try:
            job_enrichment_record = CompanyJobEnrichmentCreate(
                company_id=company_id,
                provider=self._provider.provider_name,
                raw_data=raw_response,
                job_count=len(job_listings),
            )
            enrichment_response = data_processor_repository.save_job_enrichment(
                job_enrichment_record
            )
            job_enrichment_id = enrichment_response.id
            logger.info(
                f"Saved job enrichment metadata for company {company_id} (ID: {job_enrichment_id})"
            )
        except Exception as e:
            logger.error(f"Failed to save job enrichment metadata: {str(e)}")
            # Continue even if save fails
            return []

        # Save individual job listings to job_listings collection
        if job_enrichment_id:
            try:
                job_listing_creates = []
                for job in job_listings:
                    job_create = JobListingCreate(
                        company_id=company_id,
                        job_enrichment_id=job_enrichment_id,
                        **job,  # Unpack the dict containing all job fields
                    )
                    job_listing_creates.append(job_create)

                if job_listing_creates:
                    saved_ids = job_listing_repository.save_job_listings_bulk(
                        job_listing_creates
                    )
                    logger.info(
                        f"Saved {len(saved_ids)} individual job listings to job_listings collection for company {company_id}"
                    )

                    # Save the sources for the job listings in bulk
                    try:
                        sources_data = []
                        for idx, job in enumerate(job_listings):
                            provider_info = ProviderSourceInfo(
                                job_enrichment_id=job_enrichment_id,
                                provider_job_id=job["provider_job_id"],
                                url=job["url"],
                                first_seen_at=datetime.now(),
                                last_seen_at=job.get("last_seen_at") or datetime.now(),
                            )
                            sources_data.append(
                                {
                                    "job_listing_id": saved_ids[idx],
                                    "company_id": company_id,
                                    "provider_name": self._provider.provider_name,
                                    "provider_info": provider_info,
                                }
                            )

                        if sources_data:
                            count = job_listing_source_repository.add_or_update_provider_sources_bulk(
                                sources_data
                            )
                            logger.info(
                                f"Saved {count} job listing sources for company {company_id}"
                            )
                    except Exception as e:
                        logger.error(f"Failed to save job listing sources: {str(e)}")
                        # Continue even if save fails

                    # Return the saved listings from the database
                    return job_listing_repository.get_job_listings_by_company(
                        company_id, self._provider.provider_name
                    )
            except Exception as e:
                logger.error(f"Failed to save individual job listings: {str(e)}")
                # Continue even if save fails
                return []

    def _map_job_listings_to_standard(
        self, raw_response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Map provider-specific job listings to standard dict format for JobListingCreate

        Args:
            raw_response: Raw response from provider

        Returns:
            List of dicts with job listing data
        """
        from datetime import datetime

        job_listings = []

        # Handle Apollo.io response format
        if "organization_job_postings" in raw_response:
            for job in raw_response["organization_job_postings"]:
                # Build location string
                location_parts = []
                if job.get("city"):
                    location_parts.append(job["city"])
                if job.get("state"):
                    location_parts.append(job["state"])
                if job.get("country"):
                    location_parts.append(job["country"])
                location = ", ".join(location_parts) if location_parts else None

                # Parse dates
                posted_at = None
                if job.get("posted_at"):
                    try:
                        posted_at = datetime.fromisoformat(
                            job["posted_at"]
                            .replace("+00:00", "+0000")
                            .replace("Z", "+0000")
                        )
                    except (ValueError, AttributeError):
                        pass

                last_seen_at = None
                if job.get("last_seen_at"):
                    try:
                        last_seen_at = datetime.fromisoformat(
                            job["last_seen_at"]
                            .replace("+00:00", "+0000")
                            .replace("Z", "+0000")
                        )
                    except (ValueError, AttributeError):
                        pass

                job_dict = {
                    "title": job["title"],
                    "url": job["url"],
                    "location": location,
                    "city": job.get("city"),
                    "state": job.get("state"),
                    "country": job.get("country"),
                    "posted_at": posted_at,
                    "last_seen_at": last_seen_at,
                    "provider": self._provider.provider_name,
                    "provider_job_id": job["id"],
                }

                job_listings.append(job_dict)

        return job_listings
