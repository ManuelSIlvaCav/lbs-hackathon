"""
Company API routes
"""

from fastapi import APIRouter, Query, HTTPException

from .models import CompanyResponse, CompanyCreate
from .repository import company_repository
from .providers.provider import provider_search_companies

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


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(company: CompanyCreate):
    """
    Create a new company

    Requires:
    - name: Company name (required)
    - company_url: Company website URL (required, must be valid URL)

    The domain will be automatically extracted from the company_url
    """
    from urllib.parse import urlparse

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
                "industry": c.industry,
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


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """Get a company by ID"""
    company = company_repository.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
