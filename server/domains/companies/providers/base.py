from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import CompanyModel


class CompanyInformationServiceProvider(ABC):
    @abstractmethod
    def get_company_information(self, domain: str) -> dict:
        pass

    @abstractmethod
    def search_companies(self, query: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def map_search_to_standard_list(
        self, provider_data: Dict[str, Any]
    ) -> list[CompanyModel]:
        """
        Map provider-specific data to our standard company format

        Args:
            provider_data: Raw data from the provider

        Returns:
            Dict in our standard format with keys:
            - name
            - company_url
            - industry
            - description
            - logo_url
        """
        pass

    @abstractmethod
    def get_job_listings(self, organization_id: str) -> Dict[str, Any]:
        """
        Get job listings for a company from the provider

        Args:
            organization_id: Provider-specific organization/company ID

        Returns:
            Raw response from the provider
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'apollo', 'theirstack')"""
        pass

    @abstractmethod
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
        pass
