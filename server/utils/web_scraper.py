"""
Web scraping utilities using Playwright
"""

import logging
from typing import Optional
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Page,
)

logger = logging.getLogger("app")

# Constants
DEFAULT_TIMEOUT = 60000  # 60 seconds
DEFAULT_WAIT_TIME = 4000  # 4 seconds
MAX_RETRIES = 1  # Retry once on failure
MIN_CONTENT_LENGTH = 100

# LinkedIn-specific selectors
LINKEDIN_SELECTORS = [
    ".jobs-description",
    ".job-details",
    "[id*='main-content']",
    ".details",
    "[class*='job-view']",
]

# Generic selectors for other job sites
GENERIC_SELECTORS = [
    "main",
    "[role='main']",
    ".job-description",
    ".description",
    "#job-description",
    "article",
    ".content",
]


async def scrape_job_description(
    job_url: str, timeout: int = DEFAULT_TIMEOUT
) -> Optional[str]:
    """
    Scrapes the text content from a job listing URL using Playwright.
    Includes retry mechanism (retries once on failure).

    Args:
        job_url: URL of the job listing to scrape
        timeout: Maximum time to wait for page load in milliseconds (default: 60000ms = 60s)

    Returns:
        Extracted text content from the page, or None if scraping fails after retries
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await _scrape_with_browser(job_url, timeout)
        except PlaywrightTimeoutError:
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"Timeout on attempt {attempt + 1}, retrying...",
                    extra={
                        "context": "scrape_job_description",
                        "job_url": job_url,
                        "attempt": attempt + 1,
                    },
                )
                continue
            logger.error(
                "Timeout while scraping job URL after all retries",
                extra={
                    "context": "scrape_job_description",
                    "job_url": job_url,
                    "attempts": attempt + 1,
                },
            )
            raise
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"Error on attempt {attempt + 1}, retrying...",
                    extra={
                        "context": "scrape_job_description",
                        "job_url": job_url,
                        "attempt": attempt + 1,
                        "error_msg": str(e),
                    },
                )
                continue
            logger.error(
                "Error scraping job URL after all retries",
                extra={
                    "context": "scrape_job_description",
                    "job_url": job_url,
                    "attempts": attempt + 1,
                    "error_msg": str(e),
                },
            )
            raise

    return None


async def _scrape_with_browser(job_url: str, timeout: int) -> Optional[str]:
    """Internal function to perform the actual scraping with a browser instance.

    Args:
        job_url: URL of the job listing to scrape
        timeout: Maximum time to wait for page load in milliseconds

    Returns:
        Extracted text content from the page, or None if scraping fails
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            page = await context.new_page()

            # Navigate to the URL
            response = await page.goto(
                job_url, wait_until="domcontentloaded", timeout=timeout
            )

            # Wait for dynamic content
            await page.wait_for_timeout(DEFAULT_WAIT_TIME)

            # Determine if it's a LinkedIn URL
            is_linkedin = "linkedin.com" in job_url

            # Check for redirects (especially for LinkedIn expired jobs)
            final_url = page.url
            if is_linkedin and _is_linkedin_redirect(job_url, final_url):
                logger.warning(
                    "LinkedIn job redirect detected (likely expired job)",
                    extra={
                        "context": "scrape_job_description",
                        "original_url": job_url,
                        "final_url": final_url,
                    },
                )
                # Return a marker text that the parser agent can detect
                return "PAGE_NOT_FOUND"

            # Wait for appropriate selectors
            await _wait_for_content_selectors(page, is_linkedin, job_url)

            # Remove unnecessary elements
            await _remove_unwanted_elements(page)

            # Extract text content
            text_content = await _extract_text_content(page, is_linkedin)

            # Validate and return
            return _validate_content(text_content, job_url)

        finally:
            await browser.close()


async def _wait_for_content_selectors(
    page: Page, is_linkedin: bool, job_url: str
) -> None:
    """Wait for content selectors to appear on the page.

    Args:
        page: Playwright page instance
        is_linkedin: Whether this is a LinkedIn URL
        job_url: URL being scraped (for logging)
    """
    selectors = LINKEDIN_SELECTORS if is_linkedin else GENERIC_SELECTORS
    selector_timeout = 10000 if is_linkedin else 8000

    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=selector_timeout)
            if is_linkedin:
                logger.info(
                    f"Found LinkedIn selector: {selector}",
                    extra={
                        "context": "scrape_job_description",
                        "job_url": job_url,
                    },
                )
            break
        except PlaywrightTimeoutError:
            continue


async def _remove_unwanted_elements(page: Page) -> None:
    """Remove script, style, and noscript elements from the page.

    Args:
        page: Playwright page instance
    """
    await page.evaluate(
        """
        () => {
            document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
        }
        """
    )


async def _extract_text_content(page: Page, is_linkedin: bool) -> str:
    """Extract text content from the page.

    Args:
        page: Playwright page instance
        is_linkedin: Whether this is a LinkedIn URL

    Returns:
        Extracted text content
    """
    if is_linkedin:
        text_content = await page.evaluate(
            """
            () => {
                // Try to get LinkedIn job description specifically
                const jobDesc = 
                               document.querySelector('.jobs-description') ||
                               document.querySelector('.job-details') ||
                               document.querySelector("[id*='main-content']") ||
                               document.querySelector('.details') ||
                               document.querySelector("[class*='job-view']");
                
                if (jobDesc) {
                    return jobDesc.innerText || jobDesc.textContent || '';
                }
                
                // Fallback to body if job description not found
                const body = document.body;
                return body.innerText || body.textContent || '';
            }
            """
        )
        # Clean up whitespace for LinkedIn
        return " ".join(text_content.split()).strip()
    else:
        # Get the text content for non-LinkedIn sites
        text_content = await page.evaluate(
            """
            () => {
                const body = document.body;
                const text = body.innerText || body.textContent || '';
                return text.replace(/\\s+/g, ' ').trim();
            }
            """
        )
        return text_content


def _is_linkedin_redirect(original_url: str, final_url: str) -> bool:
    """Check if LinkedIn redirected from a specific job to a generic page.

    Args:
        original_url: The URL we initially requested
        final_url: The URL we ended up on after navigation

    Returns:
        True if this appears to be a redirect indicating expired/missing job
    """
    # If URLs are the same, no redirect occurred
    if original_url == final_url:
        return False

    # Extract path from both URLs
    from urllib.parse import urlparse

    original_path = urlparse(original_url).path.lower()
    final_path = urlparse(final_url).path.lower()

    # Check if original was a specific job URL but final is generic
    # LinkedIn job URLs typically: /jobs/view/{job_id}
    if "/jobs/view/" in original_path and "/jobs/view/" not in final_path:
        return True

    # Check if redirected to main jobs page
    if final_path in ["/jobs", "/jobs/", "/jobs/search", "/jobs/search/"]:
        return True

    # Check if redirected to error/not-found page
    if "error" in final_path or "not-found" in final_path:
        return True

    return False


def _validate_content(text_content: str, job_url: str) -> Optional[str]:
    """Validate the extracted content meets minimum requirements.

    Args:
        text_content: Extracted text content
        job_url: URL being scraped (for logging)

    Returns:
        Text content if valid, or None if too short
    """
    if text_content and len(text_content) > MIN_CONTENT_LENGTH:
        logger.info(
            "Successfully scraped job description",
            extra={
                "context": "scrape_job_description",
                "job_url": job_url,
                "length": len(text_content),
                "preview": text_content,
            },
        )
        return text_content
    else:
        logger.warning(
            "Scraped text is too short or empty",
            extra={
                "context": "scrape_job_description",
                "job_url": job_url,
                "length": len(text_content) if text_content else 0,
                "text_content": text_content[:200] if text_content else None,
            },
        )
        return text_content if text_content else None
