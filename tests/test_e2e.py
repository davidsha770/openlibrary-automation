import asyncio
import json
import os
import re
import random
from playwright.async_api import async_playwright
from utils.logger_helper import setup_logger
from utils.report_generator import generate_html_report
from pages.search_page import SearchPage
from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from pages.login_page import LoginPage

# Initialize logger
logger = setup_logger()

async def search_books_by_title_under_year(query: str, max_year: int, limit: int, threshold: int, search_page):    
    """
    REQUIRED FUNCTION: Searches for books and filters them by publication year.
    Now follows POM by delegating technical work to the search_page object.
    """
    # 1. Performance measurement & Navigation
    await search_page.measure_page_performance("https://openlibrary.org/", threshold, "Homepage Load")
    
    # 2. Execute the search
    await search_page.execute_search(query)
    
    # 3. Get filtered results from the Page Object (where the logic now lives)
    found_books = await search_page.get_filtered_books(max_year, limit)
    
    if not found_books:
        logger.warning(f"No books found for query '{query}' under year {max_year}.")
        
    return found_books

async def add_books_to_reading_list(page, books: list, threshold_book, threshold_reading, book_page, reading_list_page) -> None:    
    """
    Adds found books to a random reading list after checking current library state.
    """
    logger.info("Syncing current library state using ReadingListPage...")
    want_to_read_list = await reading_list_page.get_all_book_titles("want-to-read", threshold_reading)
    already_read_list = await reading_list_page.get_all_book_titles("already-read", threshold_reading)

    for book in books:
        # Performance measurement handles navigation to book page
        await book_page.measure_page_performance(book['url'], threshold_book, f"Load Book: {book['title']}")
        book_title_clean = book['title'].lower().strip()
            
        # Randomly choose target status
        target_status = random.choice(["Want to Read", "Already Read"])
        
        # Check if the book is already in the target list to avoid redundant actions
        if target_status == "Want to Read" and book_title_clean in want_to_read_list:
            logger.info(f"SKIP: '{book['title']}' is already set to '{target_status}'.")
            continue

        if target_status == "Already Read" and book_title_clean in already_read_list:
            logger.info(f"SKIP: '{book['title']}' is already set to '{target_status}'.")
            continue
        
        try:
            logger.info(f"ADDING: '{book['title']}' to '{target_status}'")
            
            # Execute addition using the page object logic
            result = await book_page.add_to_list_specific(target_status)
            
            if result != "Failed":
                await book_page.capture_book_addition(book['title'])
            
        except Exception as e:
            logger.error(f"Error processing {book['title']}: {e}")

def normalize_text(text: str) -> str:
    """
    Standardizes text by handling curly quotes, removing special characters,
    and collapsing whitespace for robust comparison.
    """
    if not text:
        return ""
    text = text.replace("’", "'").replace("‘", "'")
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return " ".join(text.split())

async def assert_reading_list_content(expected_titles: list[str], reading_list_page, threshold):
    """
    Verifies that all expected books are present in the actual results.
    This function now focuses ONLY on the assertion logic.
    """
    actual_want = await reading_list_page.get_all_book_titles("want-to-read", threshold)
    actual_read = await reading_list_page.get_all_book_titles("already-read", threshold)
    actual_titles_from_all_lists = actual_want + actual_read
    normalized_actual = [normalize_text(t) for t in actual_titles_from_all_lists]
    missing_books = []

    for expected in expected_titles:
        norm_expected = normalize_text(expected)
        # Check if the expected title is in the combined list
        found = any(norm_expected in ne or ne in norm_expected for ne in normalized_actual)
        if not found:
            missing_books.append(expected)

    if missing_books:
        logger.error(f"Verification Failed! Missing: {missing_books}")
        raise AssertionError(f"Data Verification Failed! Missing: {missing_books}")
    
    logger.info("SUCCESS: All added books confirmed in the Reading Lists.")

async def main():
    config_path = os.path.join("config", "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    data = config["test_data"]
    urls = config["urls"]
    thresholds = config["performance_thresholds"]

    async with async_playwright() as p:
        browser = await p.chromium.launch() 
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
            creds = config.get("credentials", {})
            await login_page.login(creds.get("username"), creds.get("password"))

            urls = await search_books_by_title_under_year(
                data["search_query"], 
                data["max_year"], 
                data["results_limit"], 
                thresholds["search_page"],
                search_page
)
            
            if not urls:
                logger.warning("No matching books found during search.")
                return

            # Step 2: Add books to user's reading list
            await add_books_to_reading_list(page, urls, thresholds["book_page"], thresholds["reading_list"], book_page, reading_list_page)  
                      
            # Step 3: Verify list content
            await assert_reading_list_content(
                [b['title'] for b in urls],
                reading_list_page,
                thresholds["reading_list"]
            )
            
        except Exception as e:
            logger.error(f"E2E Execution failed: {str(e)}")
            raise e
        finally:
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