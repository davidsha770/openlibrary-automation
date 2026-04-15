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

# Load environment variables and initialize logger
load_dotenv()
logger = setup_logger()

@pytest.mark.asyncio
async def test_open_library_e2e(page):
    """
    Main E2E Test Case for OpenLibrary.
    Demonstrates POM, OOP, and Data-Driven architecture.
    """
    # 1. Load configuration (Data-Driven approach)
    config_path = os.path.join("config", "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    data = config["test_data"]
    urls = config["urls"]
    thresholds = config["performance_thresholds"]

    # 2. Initialize Page Objects
    login_page = LoginPage(page, logger)
    search_page = SearchPage(page, logger)
    book_page = BookPage(page, logger)
    reading_list_page = ReadingListPage(page, logger)

    # --- Defining required functions based on the test signature ---

    async def search_books_by_title_under_year(query: str, max_year: int, limit: int = 5) -> list[str]:
        """Search for books and filter by publication year."""
        # Measure performance for the Home/Search page load
        await search_page.measure_page_performance(urls["base_url"], thresholds["search_page"], "Search Page Load")
        await search_page.execute_search(query)
        
        # Filtering logic and Pagination are encapsulated within the Page Object
        return await search_page.get_filtered_books(urls["base_url"], max_year, limit)

    async def add_books_to_reading_list(book_urls: list[str]) -> None:
        """Add books to random reading lists (Want to Read / Already Read)."""
        for url in book_urls:
            # Navigate to each URL and measure performance
            label = url.split('/')[-1]
            await book_page.measure_page_performance(url, thresholds["book_page"], f"Load Book: {label}")
            
            # Randomize the target list
            target_status = random.choice(["Want to Read", "Already Read"])
            logger.info(f"ADDING: '{url}' to list '{target_status}'")
            
            success = await book_page.add_to_list_specific(target_status)
            if success != "Failed":
                # Capture screenshot and log for each added book
                await book_page.capture_book_addition(url)

    async def assert_reading_list_count(expected_count: int) -> None:
        """Verify the total count of books in the reading list including page load performance."""
        # 1. Navigate to the reading list page and measure its load time
        user_handle = os.getenv("OL_INER_USERNAME")
        list_url = f"{urls['base_url']}/people/{user_handle}/books/want-to-read"
        
        await reading_list_page.measure_page_performance(
            list_url, 
            thresholds.get("reading_list_page", 5000), 
            "Reading List Page Load"
        )

        # 2. Execute the logical verification (Assert)
        await reading_list_page.assert_reading_list_count(expected_count)

    # --- E2E Scenario Execution ---
    try:
        # A. Login (Prerequisite for list management)
        await login_page.login(os.getenv("OL_USERNAME"), os.getenv("OL_PASSWORD"))

        # B. Search and Filter
        found_books = await search_books_by_title_under_year(
            data["search_query"], 
            data["max_year"], 
            data.get("results_limit", 5)
        )
        
        assert len(found_books) > 0, f"No books found under year {data['max_year']}!"

        # C. Add to Lists
        await add_books_to_reading_list(found_books)

        # D. Final Verification
        await assert_reading_list_count(len(found_books))

    finally:
        # E. Cleanup and Reporting
        logger.info("Cleaning up environment...")
        try:
            # Remove added books to maintain a clean state for the next run
            await reading_list_page.clear_reading_lists(os.getenv("OL_INER_USERNAME"))
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

        # Aggregate performance data and generate reports
        final_perf_results = (
            search_page.performance_data + 
            book_page.performance_data + 
            reading_list_page.performance_data
        )
        save_performance_report(final_perf_results)
        generate_html_report(final_perf_results)
        logger.info("Reports and performance data generated successfully.")