import pytest
import allure
import json
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Imports for Page Objects
from pages.login_page import LoginPage
from pages.search_page import SearchPage
from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from utils.logger_helper import setup_logger

load_dotenv()

@pytest.fixture(scope="session")
def config():
    with open("config/config.json", "r") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def logger():
    """
    Centralized logger fixture. 
    Ensures all components use the same logging instance.
    """
    return setup_logger()

@pytest.fixture(scope="function")
async def page(logger):
    """
    Manages the Playwright browser lifecycle. 
    Note: We separate 'playwright' start from browser launch to avoid scope issues.
    """
    playwright = await async_playwright().start()
    
    is_headless = os.getenv("HEADLESS", "false").lower() == "true"
    browser = await playwright.chromium.launch(headless=is_headless)
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    page.set_default_timeout(30000)

    allure.dynamic.parameter("browser", "chromium")
    allure.dynamic.parameter("headless", is_headless)
    
    # --- YIELD THE PAGE ---
    yield page

    try:
        # --- TEARDOWN ---
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()
        logger.info("Browser context and playwright instance closed.")
    except Exception as e:
        logger.warning(f"Error during browser teardown: {e}")

@pytest.fixture(scope="function")
async def app(page, config, logger):
    """
    Factory fixture for Page Objects.
    Provides a clean interface for tests to access page-specific logic.
    """
    return {
        "login": LoginPage(page, logger, config),
        "search": SearchPage(page, logger, config),
        "book": BookPage(page, logger, config),
        "reading_list": ReadingListPage(page, logger, config),
        "config": config,
        "logger": logger
    }