import asyncio
import json
import os
import re
import random
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from utils.logger_helper import setup_logger
from utils.report_generator import generate_html_report
from pages.search_page import SearchPage
from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from pages.login_page import LoginPage

# Initialize logger
load_dotenv()
logger = setup_logger()

async def search_books_by_title_under_year(query: str, base_url, max_year: int, limit: int, threshold: int, search_page):    
    """
    REQUIRED FUNCTION: Searches for books and filters them by publication year.
    Now follows POM by delegating technical work to the search_page object.
    """
    # 1. Performance measurement & Navigation
    await search_page.measure_page_performance(base_url, threshold, "Homepage Load")
    
    # 2. Execute the search
    await search_page.execute_search(query)
    
    # 3. Get filtered results from the Page Object (where the logic now lives)
    found_books = await search_page.get_filtered_books(base_url, max_year, limit)
    
    if not found_books:
        logger.warning(f"No books found for query '{query}' under year {max_year}.")
        
    return found_books

async def add_books_to_reading_list(books: list, threshold, book_page) -> None:    
    """
    Adds found books to a random reading list after checking current library state.
    """
    logger.info("Syncing current library state using ReadingListPage...")

    for book_url in books:
        # Performance measurement handles navigation to book page
        label = book_url.split('/')[-1].replace('?', ' ')
        await book_page.measure_page_performance(book_url, threshold, f"Load Book: {label}")
            
        # Randomly choose target status
        target_status = random.choice(["Want to Read", "Already Read"])
        
        try:
            logger.info(f"ADDING: '{book_url}' to '{target_status}'")
            result = await book_page.add_to_list_specific(target_status)
            
            if result != "Failed":
                await book_page.capture_book_addition(book_url)
            
        except Exception as e:
            logger.error(f"Error processing {book_url}: {e}")

async def assert_reading_list_count(expected_count: int, reading_list_page, threshold, user_name):
    """
    Verifies the total number of books in the reading lists matches the expected count.
    """
    actual_want = await reading_list_page.get_all_book_titles("want-to-read", threshold, user_name)
    actual_read = await reading_list_page.get_all_book_titles("already-read", threshold, user_name)
    
    total_actual = len(actual_want) + len(actual_read)
    
    logger.info(f"Checking count: Expected {expected_count}, Found {total_actual}")
    
    if total_actual < expected_count:
        raise AssertionError(f"Count mismatch! Expected at least {expected_count}, but found {total_actual}")
    
async def main():
    config_path = os.path.join("config", "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    data = config["test_data"]
    urls = config["urls"]
    thresholds = config["performance_thresholds"]
    
    username = os.getenv("OL_USERNAME")
    password = os.getenv("OL_PASSWORD")
    iner_username = os.getenv("OL_INER_USERNAME")
    
    if not username or not password:
        logger.error("Credentials missing in environment variables!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Initialize Page Objects
        login_page = LoginPage(page, logger)
        search_page = SearchPage(page, logger)
        book_page = BookPage(page, logger)
        reading_list_page = ReadingListPage(page, logger)
        
        try:
            await login_page.login(username, password)

            found_books = await search_books_by_title_under_year(
                data["search_query"], 
                urls["base_url"],
                data["max_year"], 
                data["results_limit"], 
                thresholds["search_page"],
                search_page
)
            
            if found_books:
                # Step 2: Add books to user's reading list
                await add_books_to_reading_list(found_books, thresholds["book_page"], book_page)  
                        
                # Step 3: Verify list content
                await assert_reading_list_count(len(found_books), reading_list_page, thresholds["reading_list"], iner_username)
            else:
                logger.warning("No matching books found during search.")

        except Exception as e:
            logger.error(f"E2E Execution failed: {str(e)}")
            raise e
        finally:
            logger.info("Cleaning up environment...")
            try:
                await reading_list_page.clear_reading_lists(iner_username)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup failed (non-critical): {cleanup_error}")
            # Consolidate performance results from all page objects
            final_perf_results = (
                search_page.performance_data + 
                book_page.performance_data + 
                reading_list_page.performance_data
            )
            os.makedirs("outputs", exist_ok=True)
            with open("outputs/performance_report.json", "w") as f:
                json.dump(final_perf_results, f, indent=4)
            logger.info("Automation finished. Performance report generated.")
            generate_html_report(final_perf_results)
            logger.info("Report generated: outputs/report.html")
            await page.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())