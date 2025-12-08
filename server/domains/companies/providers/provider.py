from typing import List
from .company_information_service_provider import InformationServiceContext
from .implementations.apollo import apollo_provider
from ..models import CompanyModel
from domains.job_listings.models import JobListingModel

# Use singleton instance
context = InformationServiceContext(apollo_provider)


def provider_get_company_information(company_id: str, domain: str) -> CompanyModel:
    return context.enrich_and_save(company_id, domain)


def provider_search_companies(
    query: str, page: int = 1, per_page: int = 100
) -> list[CompanyModel]:
    """
    Search companies via provider and save results to repository

    Returns:
        List of CompanyModel objects mapped to our standard format
    """
    companies, _ = context.search_and_save(query=query, page=page, per_page=per_page)

    return companies


def provider_get_job_listings(
    company_id: str, provider_company_id: str
) -> List[JobListingModel]:
    """
    Get job listings for a company via provider

    Args:
        company_id: Internal company ID for saving results
        provider_company_id: Provider-specific company/organization ID

    Returns:
        List of JobListing objects in our standard format
    """
    return context.get_job_listings(company_id, provider_company_id)
