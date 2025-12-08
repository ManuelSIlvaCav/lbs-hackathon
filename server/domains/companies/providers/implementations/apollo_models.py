from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class ApolloOrganization(BaseModel):
    """Apollo.io organization data structure"""

    id: str
    name: str
    website_url: Optional[str] = None
    blog_url: Optional[str] = None
    angellist_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    primary_phone: Optional[Dict[str, Any]] = None
    languages: Optional[List[str]] = None
    alexa_ranking: Optional[int] = None
    phone: Optional[str] = None
    linkedin_uid: Optional[str] = None
    founded_year: Optional[int] = None
    publicly_traded_symbol: Optional[str] = None
    publicly_traded_exchange: Optional[str] = None
    logo_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    primary_domain: Optional[str] = None
    sanitized_phone: Optional[str] = None


class ApolloPagination(BaseModel):
    """Apollo.io pagination info"""

    page: int
    per_page: int
    total_entries: int
    total_pages: int


class ApolloSearchResponse(BaseModel):
    """Apollo.io search API response"""

    organizations: List[ApolloOrganization]
    pagination: ApolloPagination
    partial_results_only: bool = False
    breadcrumbs: Optional[List[Dict[str, Any]]] = None
    model_ids: Optional[List[str]] = None


class FundingEvent(BaseModel):
    """Funding event information"""

    id: Optional[str] = None
    date: Optional[str] = None
    news_url: Optional[str] = None
    type: Optional[str] = None
    investors: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None


class Technology(BaseModel):
    """Technology used by company"""

    uid: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None


class ApolloOrganizationEnriched(BaseModel):
    """Enriched organization data from Apollo.io"""

    id: str
    name: str
    website_url: Optional[str] = None
    blog_url: Optional[str] = None
    angellist_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    primary_phone: Optional[Dict[str, Any]] = None
    languages: Optional[List[str]] = None
    alexa_ranking: Optional[int] = None
    phone: Optional[str] = None
    linkedin_uid: Optional[str] = None
    founded_year: Optional[int] = None
    publicly_traded_symbol: Optional[str] = None
    publicly_traded_exchange: Optional[str] = None
    logo_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    primary_domain: Optional[str] = None
    industry: Optional[str] = None
    keywords: Optional[List[str]] = None
    estimated_num_employees: Optional[int] = None
    industries: Optional[List[str]] = None
    secondary_industries: Optional[List[str]] = None
    retail_location_count: Optional[int] = None
    raw_address: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    seo_description: Optional[str] = None
    short_description: Optional[str] = None
    annual_revenue_printed: Optional[str] = None
    annual_revenue: Optional[int] = None
    total_funding: Optional[int] = None
    total_funding_printed: Optional[str] = None
    latest_funding_round_date: Optional[str] = None
    latest_funding_stage: Optional[str] = None
    funding_events: Optional[List[FundingEvent]] = None
    technology_names: Optional[List[str]] = None
    current_technologies: Optional[List[Technology]] = None
    departmental_head_count: Optional[Dict[str, int]] = None


class EnrichedCompanyResponse(BaseModel):
    """Response from Apollo.io enrich endpoint"""

    organization: ApolloOrganizationEnriched


class ApolloJobPosting(BaseModel):
    """Apollo.io job posting data structure"""

    id: str
    title: str
    url: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    last_seen_at: str
    posted_at: str


class ApolloJobPostingsResponse(BaseModel):
    """Response from Apollo.io job postings endpoint"""

    organization_job_postings: List[ApolloJobPosting]
