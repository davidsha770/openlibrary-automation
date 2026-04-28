import pytest
import json
import os
import random
import allure
from utils.report_generator import generate_html_report
from utils.performance import save_performance_report

class TestOpenLibrary:
    @pytest.fixture(autouse=True, scope="function")
    async def setup_test_context(self, app):
        """
        This is the standard Way to handle class-based test state.
        It initializes everything before the test and cleans up after.
        """
        # 1. Setup: Mapping the 'app' fixture to self properties
        self.logger = app["logger"]
        self.data = app["config"]["test_data"]
        self.urls = app["config"]["urls"]
        self.thresholds = app["config"]["performance_thresholds"]
        
        # Mapping Page Objects
        self.login_page = app["login"]
        self.search_page = app["search"]
        self.book_page = app["book"]
        self.reading_list_page = app["reading_list"]

        self.username = os.getenv("OL_USERNAME")
        self.password = os.getenv("OL_PASSWORD")
        self.display_name = os.getenv("OL_DISPLAY_NAME")

        missing = [var for var in ["OL_USERNAME", "OL_PASSWORD", "OL_DISPLAY_NAME"] if not os.getenv(var)]
        if missing:
            pytest.fail(f"CRITICAL: Missing environment variables: {', '.join(missing)}. Check your .env file.")

        # 2. Execution: This is where the test actually runs
        yield 

        # 3. Teardown: This runs AFTER the test (even if it failed!)
        # No more 'finally' blocks inside the test method
        await self._perform_cleanup()

    async def _perform_cleanup(self):
        user = self.display_name
        self.logger.info("Fixture Teardown: Clearing reading lists...")
        try:
            await self.reading_list_page.clear_reading_lists(user)
        except Exception as e:
            self.logger.warning(f"Cleanup failed during teardown: {e}")

        finally:
            perf_data = (
                self.search_page.performance_data +
                self.book_page.performance_data +
                self.reading_list_page.performance_data
            )
            save_performance_report(perf_data)
            generate_html_report(perf_data)

    # --- Spec Compliant Helper Methods ---

    @allure.step("Searching for books: '{query}' (Published before {max_year})")
    async def search_books_by_title_under_year(self, query: str, max_year: int, limit: int = 5) -> list[str]:
        """Matches Spec: Only takes query, max_year, and limit."""
        await self.search_page.measure_page_performance(
            self.urls["base_url"], 
            self.thresholds["search_page"], 
            "Search Page Load"
        )
        await self.search_page.execute_search(query)
        return await self.search_page.get_filtered_books(max_year, limit)

    @allure.step("Adding discovered books to random reading lists")
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
            self.logger.info(f"ADDING: '{url}' to list '{target_status}'")
            
            success = await self.book_page.add_to_list_specific(target_status)
            if success != "Failed":
                book_slug = url.split('/')[-1].split('?')[0]
                screenshot_path = await self.book_page.capture_book_addition(book_slug)
                allure.attach.file(
                    screenshot_path, 
                    name=f"Screenshot: {book_slug}", 
                    attachment_type=allure.attachment_type.PNG
                )
                self.logger.info(f"Visual evidence attached to Allure for '{book_slug}'")

    @allure.step("Verifying final reading list count matches {expected_count}")
    async def assert_reading_list_count(self, expected_count: int) -> None:
        """Matches Spec: Only takes expected_count."""
        user_handle = self.display_name
        list_url = f"{self.urls['base_url']}/people/{user_handle}/books"
        
        await self.reading_list_page.measure_page_performance(
            list_url, 
            self.thresholds["reading_list"], 
            "Reading List Page Load"
        )
        await self.reading_list_page.assert_reading_list_count(expected_count)

    # --- Main Test Case ---
    @allure.title("E2E: Search and Manage Reading Lists")
    @pytest.mark.asyncio
    async def test_open_library_e2e(self):
        # All required data is already on 'self' thanks to the fixture
        
        # A. Login
        await self.login_page.login(self.username, self.password)

        # B. Search (Matching your exact signature)
        found_books = await self.search_books_by_title_under_year(
            self.data["search_query"],
            self.data["max_year"],
            self.data.get("results_limit", 5)
        )

        # C. Assertions & Actions
        assert len(found_books) > 0, f"No books found for query '{self.data['search_query']}' under year {self.data['max_year']}"
        await self.add_books_to_reading_list(found_books)
        await self.assert_reading_list_count(len(found_books))