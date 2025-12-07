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
