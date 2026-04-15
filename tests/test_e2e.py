import pytest
import json
import os
import random
from dotenv import load_dotenv
from utils.logger_helper import setup_logger
from utils.report_generator import generate_html_report
from utils.performance import save_performance_report
from pages.search_page import SearchPage
from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from pages.login_page import LoginPage

# Load environment variables and initialize global logger
load_dotenv()
logger = setup_logger()

class TestOpenLibrary:
    """
    E2E Test Suite for OpenLibrary.
    Organized as a class to allow helper methods to share state via 'self'
    while maintaining clean signatures according to the Spec.
    """

    async def _setup_config(self):
        """Helper to load configuration files."""
        config_path = os.path.join("config", "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        self.data = config["test_data"]
        self.urls = config["urls"]
        self.thresholds = config["performance_thresholds"]

    # --- Spec Compliant Helper Methods ---

    async def search_books_by_title_under_year(self, query: str, max_year: int, limit: int = 5) -> list[str]:
        """Matches Spec: Only takes query, max_year, and limit."""
        await self.search_page.measure_page_performance(
            self.urls["base_url"], 
            self.thresholds["search_page"], 
            "Search Page Load"
        )
        await self.search_page.execute_search(query)
        return await self.search_page.get_filtered_books(self.urls["base_url"], max_year, limit)

    async def add_books_to_reading_list(self, book_urls: list[str]) -> None:
        """Matches Spec: Only takes book_urls list."""
        for url in book_urls:
            label = url.split('/')[-1]
            await self.book_page.measure_page_performance(
                url, 
                self.thresholds["book_page"], 
                f"Load Book: {label}"
            )
            
            target_status = random.choice(["Want to Read", "Already Read"])
            logger.info(f"ADDING: '{url}' to list '{target_status}'")
            
            success = await self.book_page.add_to_list_specific(target_status)
            if success != "Failed":
                await self.book_page.capture_book_addition(url)

    async def assert_reading_list_count(self, expected_count: int) -> None:
        """Matches Spec: Only takes expected_count."""
        user_handle = os.getenv("OL_INER_USERNAME")
        list_url = f"{self.urls['base_url']}/people/{user_handle}/books/want-to-read"
        
        await self.reading_list_page.measure_page_performance(
            list_url, 
            self.thresholds["reading_list"], 
            "Reading List Page Load"
        )
        await self.reading_list_page.assert_reading_list_count(expected_count)

    # --- Main Test Case ---

    @pytest.mark.asyncio
    async def test_open_library_e2e(self, page):
        """
        Main E2E Scenario execution.
        """
        # 1. Initialize data and Page Objects
        await self._setup_config()
        self.page = page
        self.login_page = LoginPage(page, logger)
        self.search_page = SearchPage(page, logger)
        self.book_page = BookPage(page, logger)
        self.reading_list_page = ReadingListPage(page, logger)

        try:
            # A. Login
            await self.login_page.login(os.getenv("OL_USERNAME"), os.getenv("OL_PASSWORD"))

            # B. Search & Filter (Using the clean spec methods)
            found_books = await self.search_books_by_title_under_year(
                self.data["search_query"], 
                self.data["max_year"], 
                self.data.get("results_limit", 5)
            )
            
            assert len(found_books) > 0, f"No books found under year {self.data['max_year']}!"

            # C. Add to Lists
            await self.add_books_to_reading_list(found_books)

            # D. Final Verification
            await self.assert_reading_list_count(len(found_books))

        finally:
            # E. Cleanup and Reporting
            logger.info("Cleaning up environment...")
            try:
                await self.reading_list_page.clear_reading_lists(os.getenv("OL_INER_USERNAME"))
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

            # Performance reporting
            final_perf_results = (
                self.search_page.performance_data + 
                self.book_page.performance_data + 
                self.reading_list_page.performance_data
            )
            save_performance_report(final_perf_results)
            generate_html_report(final_perf_results)
            logger.info("Reports and performance data generated successfully.")