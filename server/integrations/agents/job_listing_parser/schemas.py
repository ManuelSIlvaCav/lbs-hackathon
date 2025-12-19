"""
Schema definitions for job listing categorization.

This module contains all Pydantic models used for structuring
job listing data parsed from various job boards.
"""

from enum import Enum
from pydantic import BaseModel


class AgentJobCategorizationSchema__JobInfo(BaseModel):
    """Basic job information including title, company, location, and metadata."""

    job_title: str | None = None
    company_name: str | None = None
    location: str | None = None
    industry_primary: str | None = None
    job_company_type: str | None = None
    overall_role_functions: list[str] = []

    profile_categories: list[str] = []
    role_titles: list[str] = []
    employement_type: str | None = None
    work_arrangement: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None

    experience_bullets: list[str] = []
    preferred_experience_bullets: list[str] = []


class AgentJobCategorizationSchema__ExperienceByRoleItem(BaseModel):
    """Experience requirements for a specific role function."""

    role_function: str | None = None
    experience_years_min: float | None = None
    experience_years_max: float | None = None


class AgentJobCategorizationSchema__Minimum(BaseModel):
    """Minimum/required qualifications for the job."""

    experience_years_min: float | None = None
    experience_years_max: float | None = None
    experience_by_role: list[AgentJobCategorizationSchema__ExperienceByRoleItem] = []
    role_functions: list[str] = []
    company_type_background: list[str] = []
    industry_background: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    degrees: list[str] = []
    languages: list[str] = []
    other_requirements: list[str] = []
    summary: str | None = None


class AgentJobCategorizationSchema__Preferred(BaseModel):
    """Preferred/nice-to-have qualifications for the job."""

    experience_years_min: float | None = None
    experience_years_max: float | None = None
    experience_by_role: list[AgentJobCategorizationSchema__ExperienceByRoleItem] = []
    role_functions: list[str] = []
    company_type_background: list[str] = []
    industry_background: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    degrees: list[str] = []
    languages: list[str] = []
    other_requirements: list[str] = []
    summary: str | None = None


class AgentJobCategorizationSchema__Requirements(BaseModel):
    """Container for minimum and preferred requirements."""

    minimum: AgentJobCategorizationSchema__Minimum = (
        AgentJobCategorizationSchema__Minimum()
    )
    preferred: AgentJobCategorizationSchema__Preferred = (
        AgentJobCategorizationSchema__Preferred()
    )


class AgentResult(str, Enum):
    """Possible outcomes of job parsing."""

    SUCCESS = "success"
    NO_LONGER_AVAILABLE = "no_longer_available"
    BAD_FORMAT = "bad_format"


class FailedResultError(str, Enum):
    """Types of parsing failures."""

    NO_LONGER_AVAILABLE = "no_longer_available"
    BAD_FORMAT = "bad_format"


class AgentJobCategorizationSchema(BaseModel):
    """Complete job listing categorization result."""

    job_info: AgentJobCategorizationSchema__JobInfo = (
        AgentJobCategorizationSchema__JobInfo()
    )
    requirements: AgentJobCategorizationSchema__Requirements = (
        AgentJobCategorizationSchema__Requirements()
    )
    description_summary: str | None = None
    result: AgentResult | None = None
    failed_result_error: FailedResultError | None = None


class JobCategorizationInput(BaseModel):
    """Input parameters for job categorization."""

    job_url: str
    job_id: str | None = None
