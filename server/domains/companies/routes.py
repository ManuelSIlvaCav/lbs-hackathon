"""
Company API routes
"""

from fastapi import APIRouter, Query, HTTPException
from bson import ObjectId
from urllib.parse import urlparse

from .models import CompanyCreate, CompanyModel
from .repository import company_repository
from .data_processor_repository import data_processor_repository
from domains.job_listings.models import JobListingResponse
from domains.job_listings.repository import job_listing_repository
from .providers.provider import (
    provider_get_company_information,
    provider_search_companies,
    provider_get_job_listings,
)

import logging

logger = logging.getLogger("app")

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search", response_model=dict)
async def search_companies(
    query: str = Query("", description="Search query for company name or description"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    """
    Search companies by name or description with pagination

    Returns companies matching the search query along with total count
    """
    companies, total_count = company_repository.search_companies(
        query=query, skip=skip, limit=limit
    )

    return {
        "companies": companies,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(companies) < total_count,
    }


@router.post("/", response_model=CompanyModel, status_code=201)
async def create_company(company: CompanyCreate):
    """
    Create a new company

    Requires:
    - name: Company name (required)
    - company_url: Company website URL (required, must be valid URL)

    The domain will be automatically extracted from the company_url
    """

    # Validate URL
    if not company.company_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL format. URL must start with http:// or https://",
        )

    # Extract domain from URL
    try:
        parsed_url = urlparse(company.company_url)
        domain = parsed_url.netloc

        if not domain:
            raise HTTPException(
                status_code=400, detail="Could not extract domain from URL"
            )

        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]  # Remove "www."

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL format: {str(e)}")

    # Create company data with extracted domain
    company_data = {
        "name": company.name,
        "company_url": company.company_url,
        "domain": domain,
    }

    return company_repository.create_company(company_data)


@router.get("/provider-search", response_model=dict)
async def search_companies_via_provider(
    query: str = Query("", description="Search query for company name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=101, description="Results per page"),
):
    """
    Search companies via external provider (Apollo.io) and save results

    This endpoint:
    - Searches Apollo.io for companies matching the query
    - Maps results to our CompanyModel format
    - Saves raw search results to the repository for tracking

    Returns mapped companies ready for import
    """
    try:
        companies = provider_search_companies(query, page, per_page)

        # Convert CompanyModel objects to dicts for JSON serialization
        companies_data = [
            {
                "name": c.name,
                "company_url": c.company_url,
                "linkedin_url": c.linkedin_url,
                "logo_url": c.logo_url,
                "domain": c.domain,
                "industries": c.industries,
                "description": c.description,
            }
            for c in companies
        ]

        return {
            "companies": companies_data,
            "total": len(companies_data),
            "page": page,
            "per_page": per_page,
            "provider": "apollo",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider search failed: {str(e)}")


@router.post("/{company_id}/lookup-details", response_model=CompanyModel)
async def lookup_company_details(company_id: str):
    """
    Enrich company data using Apollo.io API

    This endpoint:
    1. Fetches the company from database by ID
    2. Uses the company's domain to lookup details via Apollo.io
    3. Saves the enrichment data for tracking
    4. Updates the company with enriched information (description, industries, logo, etc.)

    Returns the updated company data
    """

    # Get company from database
    company_doc = company_repository.collection.find_one({"_id": ObjectId(company_id)})
    if not company_doc:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check if company has a domain
    domain = company_doc.get("domain")
    if not domain:
        raise HTTPException(
            status_code=400,
            detail="Company does not have a domain. Cannot enrich without domain.",
        )

    # Call Apollo.io to get enriched data
    try:
        logger.info(f"Enriching company {company_id} with domain: {domain}")
        company = provider_get_company_information(company_id, domain)
        logger.info(f"Received enrichment data for {company_id}")

        return company

    except Exception as e:
        logger.error(f"Failed provider_get_company_information {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch enrichment data: {str(e)}"
        )


@router.get("/{company_id}", response_model=CompanyModel)
async def get_company(company_id: str):
    """Get a company by ID"""
    company = company_repository.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/{company_id}/job-listings", response_model=list[JobListingResponse])
async def get_company_job_listings(
    company_id: str,
    force_refresh: bool = Query(False, description="Force refresh from provider"),
):
    """
    Get job listings for a company

    This endpoint:
    1. First checks if job listings exist in the database
    2. If found, returns cached job listings (unless force_refresh=true)
    3. If not found or force_refresh=true, fetches from provider and saves to database
    4. Returns job listings in our standard format

    Query Parameters:
    - force_refresh: Set to true to bypass cache and fetch fresh data from provider

    Returns a list of job postings for the company
    """

    # Get company from database
    company = company_repository.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Try to get cached job listings first (unless force refresh requested)
    if not force_refresh:
        try:
            logger.info(f"Checking cached job listings for company {company_id}")
            cached_job_listings = job_listing_repository.get_job_listings_by_company(
                company_id
            )
            if cached_job_listings:
                logger.info(
                    f"Returning {len(cached_job_listings)} cached job listings for company {company_id}"
                )
                return cached_job_listings
        except Exception as e:
            logger.error(
                f"Failed to fetch cached job listings returning empty: {str(e)}"
            )
            return []

    # No cached listings or force refresh - fetch from provider
    logger.info(
        f"Fetching fresh job listings from provider for company {company_id}"
        + (" (force refresh)" if force_refresh else " (no cache)")
    )

    # Get latest enrichment to find provider company ID
    enrichment = data_processor_repository.get_latest_enrichment(company_id)
    if not enrichment:
        raise HTTPException(
            status_code=400,
            detail="Company has not been enriched yet. Please enrich the company first.",
        )

    # Extract provider company ID from enrichment data
    provider_company_id = (
        enrichment.get("raw_data", {}).get("organization", {}).get("id")
    )
    if not provider_company_id:
        raise HTTPException(
            status_code=400,
            detail="Could not find provider company ID in enrichment data.",
        )

    # Call provider to get job listings (this will also save them to the database)
    try:
        logger.info(
            f"Fetching job listings for company {company_id} (provider ID: {provider_company_id})"
        )
        job_listings = provider_get_job_listings(company_id, provider_company_id)
        logger.info(
            f"Retrieved and saved {len(job_listings)} job listings for company {company_id}"
        )

        return job_listings

    except Exception as e:
        logger.error(f"Failed to fetch job listings for company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch job listings: {str(e)}"
        )
