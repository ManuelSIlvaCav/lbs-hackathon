"""
Web scraping utilities using Playwright
"""

from typing import Optional
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


async def scrape_job_description(job_url: str, timeout: int = 60000) -> Optional[str]:
    """
    Scrapes the text content from a job listing URL using Playwright.
    Waits for JavaScript to load and extracts all visible text.

    Args:
        job_url: URL of the job listing to scrape
        timeout: Maximum time to wait for page load in milliseconds (default: 60000ms = 60s)

    Returns:
        Extracted text content from the page, or None if scraping fails
    """
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)

            # Create a new browser context with viewport
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            # Create a new page
            page = await context.new_page()

            print(f"Loading job URL: {job_url}")

            # Navigate to the URL and wait for network to be idle
            await page.goto(job_url, wait_until="domcontentloaded", timeout=timeout)

            # Wait a bit more for any dynamic content to load
            await page.wait_for_timeout(2000)

            # Try to wait for common job description containers
            # This helps ensure the main content is loaded
            selectors_to_try = [
                "main",
                "[role='main']",
                ".job-description",
                ".description",
                "#job-description",
                "article",
                ".content",
            ]

            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    print(f"Found content container: {selector}")
                    break
                except PlaywrightTimeoutError:
                    continue
            print("Proceeding to extract text content...")

            # Extract all visible text from the page
            # Remove script and style elements first
            await page.evaluate(
                """
                () => {
                    // Remove script and style elements
                    document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                }
            """
            )

            # Get the text content
            text_content = await page.evaluate(
                """
                () => {
                    // Get text from body, cleaning up whitespace
                    const body = document.body;
                    const text = body.innerText || body.textContent || '';
                    // Clean up multiple spaces and newlines
                    return text.replace(/\\s+/g, ' ').trim();
                }
            """
            )

            # Close the browser
            await browser.close()

            if text_content and len(text_content) > 100:
                print(
                    f"Successfully scraped {len(text_content)} characters from {job_url}"
                )
                return text_content
            else:
                print(f"Warning: Scraped text is too short ({len(text_content)} chars)")
                return text_content if text_content else None

    except PlaywrightTimeoutError:
        print(f"Timeout error while loading {job_url}")
        return None
    except Exception as e:
        print(f"Error scraping job URL {job_url}: {e}")
        return None
