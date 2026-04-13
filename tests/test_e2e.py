import asyncio
import json
import os
import re
import random
from playwright.async_api import async_playwright
from utils.logger_helper import setup_logger
from pages.search_page import SearchPage
from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage

# Initialize logger
logger = setup_logger()

async def login(page, config):
    """
    Performs login before starting the E2E flow.
    """
    logger.info("Starting login process...")
    creds = config.get("credentials", {})
    username = creds.get("username")
    password = creds.get("password")

    if not username or not password or "YOUR_ACTUAL" in username:
        logger.error("Missing or dummy credentials in config.json!")
        raise ValueError("Please update config/config.json with real credentials.")

    await page.goto("https://openlibrary.org/account/login")
    await page.fill("input[name='username']", username)
    await page.fill("input[name='password']", password)
    await page.click("button[type='submit']")

async def search_books_by_title_under_year(page, query: str, max_year: int, limit: int, threshold: int, search_page):    
    """
    Searches for books and filters them by publication year.
    """
    # measure_page_performance already handles page.goto
    await search_page.measure_page_performance("https://openlibrary.org/", threshold, "Homepage Load")
    
    await search_page.execute_search(query)
    
    found_books = []
    base_url = "https://openlibrary.org"

    while len(found_books) < limit:
        results = await search_page.get_results_on_page()
        
        for item in results:
            if len(found_books) >= limit:
                break
                
            year_el = await item.query_selector(search_page.PUBLICATION_YEAR_TEXT)
            if year_el:
                year_text = await year_el.inner_text()
                year = await search_page.extract_year_from_text(year_text)
                
                if year and year < max_year:
                    link_el = await item.query_selector(search_page.BOOK_TITLE_LINK)
                    if link_el:
                        title = await link_el.inner_text()
                        href = await link_el.get_attribute("href")
                        found_books.append({
                            "title": title.strip(),
                            "url": base_url + href
                        })
                        logger.info(f"MATCH: {title.strip()} ({year})")
        
        if len(found_books) < limit:
            if not await search_page.go_to_next_page():
                break
                
    return found_books

async def fetch_existing_books(page, list_type: str) -> list:
    """
    Retrieves book titles from a specific reading list (want-to-read or already-read).
    """
    url = f"https://openlibrary.org/people/user532228/books/{list_type}"
    await page.goto(url, wait_until="networkidle")
    # Extract and normalize titles for comparison
    titles = await page.locator("h3.booktitle a").all_inner_texts()
    return [t.lower().strip() for t in titles]

async def add_books_to_reading_list(page, books: list, threshold, book_page) -> None:    
    """
    Adds found books to a random reading list after checking current library state.
    """
    logger.info("Syncing current library state...")
    want_to_read_list = await fetch_existing_books(page, "want-to-read")
    already_read_list = await fetch_existing_books(page, "already-read")

    for book in books:
        # Performance measurement handles navigation to book page
        await book_page.measure_page_performance(book['url'], threshold, f"Load Book: {book['title']}")
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
            await page.wait_for_timeout(2000)
            logger.info(f"ADDING: '{book['title']}' to '{target_status}'")
            
            # Execute addition using the page object logic
            result = await book_page.add_to_list_specific(target_status)
            
            if result != "Failed":
                await book_page.capture_book_addition(book['title'])
            
            await page.wait_for_timeout(2000)
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

async def assert_reading_list_content(page, expected_titles: list[str], list_urls: list[str], threshold, reading_list_page) -> None:
    """
    Verifies that all expected books are present across the provided Reading Lists.
    """
    all_normalized_existing = []

    for url in list_urls:
        # Measure navigation to reading list
        await reading_list_page.measure_page_performance(url, threshold, f"Verify List: {url.split('/')[-1]}")
        logger.info(f"Checking reading list: {url}")
        try:
            # Wait for Web Components Hydration
            await page.wait_for_timeout(5000)
            
            # Fetch and normalize titles from the current list
            titles = await reading_list_page.get_all_book_titles()
            normalized_for_this_list = [normalize_text(t) for t in titles]
            all_normalized_existing.extend(normalized_for_this_list)
            
            logger.info(f"Found {len(titles)} titles in {url.split('/')[-1]}")
            
        except Exception as e:
            logger.error(f"Failed to fetch list from {url}: {e}")

    all_normalized_existing = list(set(all_normalized_existing))

    missing_books = []
    for expected in expected_titles:
        norm_expected = normalize_text(expected)
        
        # Verify if the expected title exists in the combined list data
        found = any(norm_expected in ne or ne in norm_expected for ne in all_normalized_existing)
        
        if not found:
            missing_books.append(expected)

    logger.info(f"Unique titles found across all lists: {len(all_normalized_existing)}")
            
    if not missing_books:
        logger.info("SUCCESS: All added books confirmed across the Reading Lists.")
    else:
        await page.screenshot(path="outputs/screenshots/verification_failed.png")
        logger.error(f"Verification Failed! Missing: {missing_books}")
        raise AssertionError(f"Data Verification Failed! Missing: {missing_books}")
          
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
        search_page = SearchPage(page, logger)
        book_page = BookPage(page, logger)
        reading_list_page = ReadingListPage(page, logger)
        
        try:
            await login(page, config)

            # Step 1: Search based on criteria
            found_books = await search_books_by_title_under_year(
                page, data["search_query"], data["max_year"], 
                data["results_limit"], thresholds["search_page"],
                search_page
            )
            
            if not found_books:
                logger.warning("No matching books found during search.")
                return

            # Step 2: Add books to user's reading list
            await add_books_to_reading_list(page, found_books, thresholds["book_page"], book_page)  
                      
            # Step 3: Verify list content
            titles = [b['title'] for b in found_books]
            await assert_reading_list_content(
                page, 
                titles, 
                [
                    "https://openlibrary.org/people/user532228/books/want-to-read",
                    "https://openlibrary.org/people/user532228/books/already-read"
                ],
                thresholds["reading_list"],
                reading_list_page
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
            await page.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())