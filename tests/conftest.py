import pytest
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

# Load environment variables from .env file (e.g., HEADLESS, credentials)
load_dotenv()

@pytest.fixture
async def page():
    """
    Pytest fixture to initialize and manage the Playwright browser lifecycle.
    Configures the browser context with anti-bot headers and standard resolution.
    """
    async with async_playwright() as p:
        # Toggle headless mode via environment variable for CI/CD flexibility
        is_headless = os.getenv("HEADLESS", "true").lower() == "true"
        
        browser = await p.chromium.launch(headless=is_headless)
        
        # Create a browser context with a real-world User Agent to avoid bot detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        
        # Set a global timeout (30s) to prevent tests from hanging indefinitely
        context.set_default_timeout(30000)
        
        page = await context.new_page()
        
        # Provide the page object to the test
        yield page

        # Cleanup: Ensure resources are released after test completion to prevent memory leaks
        await context.close()
        await browser.close()