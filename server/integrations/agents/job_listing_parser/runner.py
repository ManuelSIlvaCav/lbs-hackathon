"""
Job listing parser runner module.

This module contains the main execution logic for running
the job listing parser workflow, including web scraping
and agent orchestration.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from agents import Runner

from utils.open_ai_singleton import OpenAISingleton
from utils.web_scraper import scrape_job_description

from .schemas import AgentJobCategorizationSchema, JobCategorizationInput
from .agents import linkedin_parser_agent, other_job_parser_agent


logger = logging.getLogger("app")


def is_linkedin_url(url: str) -> bool:
    """
    Check if a URL is from LinkedIn.

    Args:
        url: The job URL to check.

    Returns:
        True if the URL is from LinkedIn, False otherwise.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return "linkedin.com" in domain or domain.endswith(".linkedin.com")
    except Exception:
        return False


async def run_agent_job_categorization(
    categorization_input: JobCategorizationInput,
) -> Optional[AgentJobCategorizationSchema]:
    """
    Run the job listing parser workflow.

    This function orchestrates the complete job parsing process:
    1. Scrapes the job description from the provided URL using Playwright
    2. Determines the appropriate parser based on URL domain
    3. Sends content to the specialized parser (LinkedIn or Other)
    4. Returns the parsed and categorized job listing data

    Args:
        categorization_input: Input containing the job_url to parse and optional job_id.

    Returns:
        Parsed job listing data as AgentJobCategorizationSchema if successful,
        None if scraping or parsing fails.

    Raises:
        Exception: If an error occurs during parsing (after logging).
    """
    try:
        # Step 1: Scrape the job description from the URL using Playwright
        job_text = await scrape_job_description(categorization_input.job_url)

        if not job_text:
            logger.error(
                "Failed to scrape content",
                extra={
                    "context": "job_listing_parsing",
                    "job_url": categorization_input.job_url,
                },
            )
            return None

        if job_text == "PAGE_NOT_FOUND":
            logger.info(
                "Job page not found or redirected",
                extra={
                    "context": "job_listing_parsing",
                    "job_url": categorization_input.job_url,
                },
            )
            return None

        # Step 2: Determine which parser to use based on URL domain
        is_linkedin = is_linkedin_url(categorization_input.job_url)
        selected_agent = (
            linkedin_parser_agent if is_linkedin else other_job_parser_agent
        )
        parser_type = "LinkedIn" if is_linkedin else "Other"

        logger.info(
            f"Routing to {parser_type} parser based on URL domain",
            extra={
                "context": "job_listing_parsing",
                "job_url": categorization_input.job_url,
                "parser_type": parser_type,
            },
        )

        # Step 3: Send the scraped text to the appropriate specialized parser
        result = await Runner.run(
            selected_agent,
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Please parse the following job description:\n\n{job_text}",
                        }
                    ],
                }
            ],
        )

        usage = result.context_wrapper.usage
        rate_limit_info = OpenAISingleton.get_rate_limits()

        logger.info(
            f"Successfully parsed job listing via {parser_type} parser",
            extra={
                "context": "job_listing_parsing",
                "job_url": categorization_input.job_url,
                "parser_type": parser_type,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "rate_limit_info": rate_limit_info,
                "job_id": (
                    categorization_input.job_id
                    if categorization_input.job_id
                    else "On creation"
                ),
            },
        )
        return result.final_output

    except Exception as e:
        logger.error(
            f"Error running Job parser",
            extra={
                "context": "job_listing_parsing",
                "job_url": categorization_input.job_url,
                "error_msg": str(e),
            },
        )
        raise Exception(f"Error running Job parser: {str(e)}") from e
