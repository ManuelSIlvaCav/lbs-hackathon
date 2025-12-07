from .company_information_service_provider import InformationServiceContext
from .implementations.apollo import apollo_provider
from ..models import CompanyModel

# Use singleton instance
context = InformationServiceContext(apollo_provider)


def get_company_info(name: str) -> dict:
    return context.get_company_info(name)


def provider_search_companies(
    query: str, page: int = 1, per_page: int = 100
) -> list[CompanyModel]:
    """
    Search companies via provider and save results to repository

    Returns:
        List of CompanyModel objects mapped to our standard format
    """
    companies, apollo_response = apollo_provider.search_and_save(
        query=query, page=page, per_page=per_page
    )

    return companies
