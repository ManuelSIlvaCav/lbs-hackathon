import time
from typing import Any, Dict, List
import logging

from domains.job_listings.source_repository import job_listing_source_repository

from .base import CompanyInformationServiceProvider

from ..enrichment_models import CompanyEnrichmentCreate, CompanyJobEnrichmentCreate
from ..models import CompanyModel
from domains.job_listings.models import JobListingModel, JobListingCreate
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
            logger.error(
                f"Enrichment failed for company {company_id}: missing organization data {response}"
            )
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
        self, company_id: str, organization_id: str, force_refresh: bool = True
    ) -> List[JobListingModel]:
        """
        Get job listings for a company from the provider and save results

        Args:
            company_id: Internal company ID for saving results
            organization_id: Provider-specific organization/company ID

        Returns:
            List of JobListingModel objects in our standard format
        """
        if force_refresh:
            # Get raw response from provider
            raw_response = self._provider.get_job_listings(organization_id)
        else:
            logger.info(
                "Checking for latest cached job enrichment data",
                extra={
                    "context": "get_job_listings",
                    "company_id": company_id,
                    "provider": self._provider.provider_name,
                },
            )
            latest_job_enrichment = data_processor_repository.get_latest_job_enrichment(
                company_id=company_id, provider=self._provider.provider_name
            )
            raw_response = (
                latest_job_enrichment["raw_data"] if latest_job_enrichment else None
            )

        if not raw_response:
            logger.warning(
                f"No job listings data available",
                extra={
                    "context": "get_job_listings",
                    "company_id": company_id,
                    "provider": self._provider.provider_name,
                },
            )
            return []

        # Map provider response to our standard JobListing format
        job_listings = self._map_job_listings_to_standard(raw_response)

        if force_refresh:
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
        else:
            job_enrichment_id = (
                latest_job_enrichment["_id"] if latest_job_enrichment else None
            )

        # Sync job listings with smart upsert logic
        if job_enrichment_id:
            return self._sync_job_listings(
                company_id=company_id,
                job_listings=job_listings,
                job_enrichment_id=job_enrichment_id,
            )

        return []

    def _sync_job_listings(
        self,
        company_id: str,
        job_listings: List[Dict[str, Any]],
        job_enrichment_id: str,
    ) -> List[JobListingModel]:
        """
        Sync job listings with smart upsert logic:
        1. Insert new jobs (by URL)
        2. Update existing jobs (last_seen_at, posted_at)
        3. Mark missing jobs as expired

        Args:
            company_id: Internal company ID
            job_listings: List of job listing dicts from provider
            job_enrichment_id: ID of the job enrichment record

        Returns:
            List of JobListingModel objects from database
        """
        try:
            # Prepare JobListingCreate objects
            job_listing_creates = []
            url_to_provider_data = {}  # Map URL to provider-specific data

            for job in job_listings:
                # Extract only JobListingCreate-compatible fields
                job_create_data = {k: v for k, v in job.items()}
                job_create = JobListingCreate(**job_create_data)
                job_listing_creates.append(job_create)

                # Store provider-specific data for source tracking
                url_to_provider_data[job["url"]] = {
                    "provider_job_id": job["provider_job_id"],
                    "url": job["url"],
                    "last_seen_at": job.get("last_seen_at"),
                }

            if not job_listing_creates:
                logger.warning(
                    f"No valid job listings to sync for company {company_id}"
                )
                return []

            logger.info(
                "Syncing job listings for company",
                extra={
                    "company_id": company_id,
                    "provider": self._provider.provider_name,
                    "job_enrichment_id": job_enrichment_id,
                    "job_count": len(job_listing_creates),
                },
            )

            start_time = time.perf_counter()

            # Upsert job listings with smart logic
            inserted_ids, updated_ids, expired_count = (
                job_listing_repository.upsert_job_listings_bulk(
                    company_id=company_id,
                    job_listings=job_listing_creates,
                )
            )

            elapsed_time = time.perf_counter() - start_time

            logger.info(
                "Job listings sync summary",
                extra={
                    "company_id": company_id,
                    "inserted_count": len(inserted_ids),
                    "updated_count": len(updated_ids),
                    "expired_count": expired_count,
                    "elapsed_time": round(elapsed_time, 2),
                },
            )

            # Sync provider sources for inserted and updated jobs
            start_time_sources = time.perf_counter()
            try:
                count = job_listing_source_repository.sync_provider_sources_for_jobs(
                    inserted_ids=inserted_ids,
                    updated_ids=updated_ids,
                    company_id=company_id,
                    provider_name=self._provider.provider_name,
                    job_enrichment_id=job_enrichment_id,
                    url_to_provider_data=url_to_provider_data,
                )
                elapsed_time_sources = time.perf_counter() - start_time_sources

                logger.info(
                    "Saved job listing sources data",
                    extra={
                        "count": count,
                        "elapsed_time": round(elapsed_time_sources, 2),
                    },
                )

            except Exception as e:
                logger.error(
                    "Failed to sync provider sources",
                    extra={"error_msg": str(e)},
                )
                # Continue even if source save fails
            # Return all active job listings for this company
            return job_listing_repository.get_job_listings_by_company(company_id)

        except Exception as e:
            logger.error(f"Failed to sync job listings: {str(e)}")
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
                        logger.error(
                            f"Failed to parse posted_at date for job",
                            extra={
                                "context": "map_job_listings_to_standard",
                                "posted_at": job["posted_at"],
                            },
                        )
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
                        logger.error(
                            f"Failed to parse last_seen_at date for job",
                            extra={
                                "context": "map_job_listings_to_standard",
                                "last_seen_at": job["last_seen_at"],
                            },
                        )
                        pass

                # Note: provider and provider_job_id kept in dict for source tracking
                # but won't be passed to JobListingCreate (not in that model)
                job_dict = {
                    "title": job["title"],
                    "url": job["url"],
                    "location": location,
                    "city": job.get("city"),
                    "state": job.get("state"),
                    "country": job.get("country"),
                    "posted_at": posted_at,
                    "last_seen_at": last_seen_at,
                    "provider": self._provider.provider_name,  # For source tracking only
                    "provider_job_id": job["id"],  # For source tracking only
                    "source_status": "scrapped",
                }

                job_listings.append(job_dict)

        return job_listings
