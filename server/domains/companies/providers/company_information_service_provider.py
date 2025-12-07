from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import CompanyModel


class CompanyInformationServiceProvider(ABC):
    @abstractmethod
    def get_company_information(self, name: str) -> dict:
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

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'apollo', 'theirstack')"""
        pass


class InformationServiceContext:
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, provider: CompanyInformationServiceProvider) -> None:
        """
        Usually, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._provider = provider

    @property
    def provider(self) -> CompanyInformationServiceProvider:
        """
        The Context maintains a reference to one of the Provider objects. The
        Context does not know the concrete class of a provider. It should work
        with all providers via the Provider interface.
        """

        return self._provider

    @provider.setter
    def provider(self, provider: CompanyInformationServiceProvider) -> None:
        """
        Usually, the Context allows replacing a Provider object at runtime.
        """

        self._provider = provider

    def get_company_info(self, name: str) -> None:
        """
        The Context delegates some work to the Provider object instead of
        implementing multiple versions of the algorithm on its own.
        """

        print("Context: Getting company information")
        result = self._provider.get_company_information(name)
        print(result)
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
