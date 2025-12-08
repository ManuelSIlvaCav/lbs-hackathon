"""
Apollo.io provider implementation
"""

import logging
import os
import requests
from typing import List, Optional
from datetime import datetime

from .apollo_models import (
    ApolloSearchResponse,
    EnrichedCompanyResponse,
)
from ..company_information_service_provider import (
    CompanyInformationServiceProvider,
)
from ..repository import company_search_repository
from ..models import CompanySearchResultCreate
from ...models import CompanyModel


logger = logging.getLogger("app")


class ApolloProvider(CompanyInformationServiceProvider):
    """Apollo.io API provider for company information"""

    def __init__(self):
        self.api_key = os.getenv("APOLLO_API_KEY")
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

    @property
    def provider_name(self) -> str:
        return "apollo"

    def search_companies(
        self,
        query: str,
        page: int = 1,
        per_page: int = 100,
        organization_locations: Optional[List[str]] = None,
        organization_num_employees_ranges: Optional[List[str]] = None,
        **kwargs,
    ) -> ApolloSearchResponse:
        """
        Search for companies using Apollo.io API

        Args:
            query: Company name or domain to search
            page: Page number (default: 1)
            per_page: Results per page (default: 10)
            organization_locations: List of location filters
            organization_num_employees_ranges: List of employee count ranges
            **kwargs: Additional Apollo.io filters

        Returns:
            Dict containing Apollo search response
        """
        url = f"{self.base_url}/mixed_companies/search"

        payload = {
            "q_organization_name": query,
            "page": page,
            "per_page": per_page,
        }

        # Add optional filters
        if organization_locations:
            payload["organization_locations"] = organization_locations

        if organization_num_employees_ranges:
            payload["organization_num_employees_ranges"] = (
                organization_num_employees_ranges
            )

        # Add any additional filters
        payload.update(kwargs)

        try:
            logger.info("Apollo API Request", extra={"payload": payload, "url": url})
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error: {str(e)}")
            raise Exception(f"Apollo API error: {str(e)}")

    def get_company_information(self, identifier: str) -> EnrichedCompanyResponse:
        """
        Get detailed company information by domain

        Args:
            identifier: Company domain (e.g., 'apollo.io')

        Returns:
            Dict containing company information
        """
        url = f"{self.base_url}/organizations/enrich?domain={identifier}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Apollo API error: {str(e)}")

    def map_search_to_standard_list(
        self, provider_data: ApolloSearchResponse
    ) -> list[CompanyModel]:
        """
        Map Apollo.io organization list data to our standard format

        Args:
            provider_data: Apollo search response with organizations

        Returns:
            List of CompanyModel objects in our standard format
        """
        companies = []

        for org in provider_data.organizations:
            # Build description from available data
            description_parts = []

            if org.founded_year:
                description_parts.append(f"Founded in {org.founded_year}")

            if org.publicly_traded_symbol:
                exchange = org.publicly_traded_exchange or ""
                description_parts.append(
                    f"Publicly traded: {exchange}:{org.publicly_traded_symbol}"
                )

            if org.languages:
                langs = ", ".join(org.languages)
                description_parts.append(f"Languages: {langs}")

            if org.alexa_ranking:
                description_parts.append(f"Alexa ranking: {org.alexa_ranking}")

            description = ". ".join(description_parts) if description_parts else None

            # Create CompanyModel
            company = CompanyModel(
                name=org.name,
                company_url=org.website_url,
                linkedin_url=org.linkedin_url,
                logo_url=org.logo_url,
                domain=org.primary_domain,
                industries=None,  # Will be populated from enrichment
                description=description,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            companies.append(company)

        return companies

    def search_and_save(
        self, query: str, page: int = 1, per_page: int = 100, **kwargs
    ) -> tuple[list[CompanyModel], ApolloSearchResponse]:
        """
        Search companies via Apollo API and save results to repository

        Args:
            query: Company name to search
            page: Page number
            per_page: Results per page
            **kwargs: Additional filters

        Returns:
            Tuple of (mapped companies list, raw Apollo response)
        """
        # Search via Apollo API
        raw_response = self.search_companies(query, page, per_page, **kwargs)

        # Parse response
        apollo_response = ApolloSearchResponse(**raw_response)

        # Map to our standard format
        companies = self.map_search_to_standard_list(apollo_response)

        logger.info(f"Apollo search parsed", extra={"companies": companies})

        # Save search result to repository
        search_result_data = CompanySearchResultCreate(
            provider=self.provider_name, search_query=query, raw_data=raw_response
        )

        company_search_repository.save_search_result(search_result_data)

        logger.info("Saved Apollo search result to repository")

        return companies, apollo_response

    def get_job_listings(self, organization_id: str) -> dict:
        """
        Get job listings for a company from Apollo.io

        Args:
            organization_id: Apollo.io organization ID

        Returns:
            Raw response from Apollo API
        """
        url = f"{self.base_url}/organizations/{organization_id}/job_postings"

        try:
            logger.info(f"Fetching job listings for organization {organization_id}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            raw_response = response.json()
            logger.info(
                f"Retrieved job listings from Apollo for organization {organization_id}"
            )

            return raw_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error fetching job listings: {str(e)}")
            raise Exception(f"Apollo API error: {str(e)}")


# Singleton instance
apollo_provider = ApolloProvider()
