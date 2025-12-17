"""
Job Listing Parser Agent Module.

This module provides a clean, modular architecture for parsing job listings
from various sources (LinkedIn, other job boards, company career pages).

Architecture:
- schemas.py: Pydantic models for job data structures
- instructions.py: Agent instruction prompts (LinkedIn, Other, Orchestrator)
- agents.py: Agent definitions and factory functions
- runner.py: Main execution logic with web scraping integration

Usage:
    from integrations.agents.job_listing_parser import (
        run_agent_job_categorization,
        JobCategorizationInput,
        AgentJobCategorizationSchema,
    )

    result = await run_agent_job_categorization(
        JobCategorizationInput(
            job_url="https://example.com/job",
            job_id="optional_id"
        )
    )
"""

from .schemas import (
    AgentJobCategorizationSchema,
    AgentJobCategorizationSchema__JobInfo,
    AgentJobCategorizationSchema__Requirements,
    AgentJobCategorizationSchema__Minimum,
    AgentJobCategorizationSchema__Preferred,
    AgentResult,
    FailedResultError,
    JobCategorizationInput,
)
from .agents import (
    linkedin_parser_agent,
    other_job_parser_agent,
)
from .runner import run_agent_job_categorization

__all__ = [
    # Main entry point
    "run_agent_job_categorization",
    # Input/Output schemas
    "JobCategorizationInput",
    "AgentJobCategorizationSchema",
    "AgentJobCategorizationSchema__JobInfo",
    "AgentJobCategorizationSchema__Requirements",
    "AgentJobCategorizationSchema__Minimum",
    "AgentJobCategorizationSchema__Preferred",
    "AgentResult",
    "FailedResultError",
    # Agent instances (for testing/debugging)
    "linkedin_parser_agent",
    "other_job_parser_agent",
]
