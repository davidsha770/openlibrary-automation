from contextvars import ContextVar
import allure
import random
import asyncio

from utils.visuals import capture_book_addition
from utils.decorators import retry_on_failure

# Global registry initialized by the Test Fixture
app_context: ContextVar[dict] = ContextVar("app_context")

@allure.step("Workflow: User Authentication")
@retry_on_failure(times=2, delay=5) # Decorator protects the entire flow sequence
async def login_to_open_library(email: str, password: str):
    app = app_context.get()
    login_page = app["login"]
    logger = app["logger"]

    logger.info(f"Starting login flow for user: {email}")
    await login_page.navigate()
    
    # Step 1: Handle initial security challenges (e.g., Cloudflare)
    await login_page.handle_security_challenges()

    # Step 2: Fill credentials and submit
    await login_page.fill_credentials(email, password)
    
    # Step 3: Verify successful authentication
    if not await login_page.is_logged_in():
        # If verification fails, check if a challenge appeared after submission
        logger.warning("Initial login verification failed. Checking for post-submit challenges...")
        await login_page.handle_security_challenges()
        
        # Final verification check
        if not await login_page.is_logged_in():
            raise Exception("Authentication Failed: User is not logged in after all attempts.")

    logger.info("Authentication successful.")

@allure.step("Spec Flow: search_books_by_title_under_year")
async def search_books_by_title_under_year(query: str, max_year: int, limit: int = 5) -> list[str]:
    app = app_context.get()
    search_page = app["search"]
    urls = app["config"]["urls"]
    thresholds = app["config"]["performance_thresholds"]

    # Measure performance during the initial navigation
    await search_page.measure_page_performance(
        urls["base_url"], 
        thresholds["search_page"], 
        "Search Page Load"
    )
    
    await search_page.execute_search(query)
    found_books = []
    
    while len(found_books) < limit:
        # Business Logic: Extract raw metadata from the current result page
        raw_data = await search_page.get_current_page_results()
        
        # Filtering logic based on target criteria
        for entry in raw_data:
            year = entry['year']
            if year and year <= max_year:
                found_books.append(entry['href'])
                if len(found_books) >= limit: 
                    break
        
        # Handle pagination if the limit hasn't been reached
        if len(found_books) < limit:
            if not await search_page.navigate_to_next_page(): 
                break
            
    return found_books
    
@allure.step("Spec Flow: add_books_to_reading_list")
async def add_books_to_reading_list(book_urls: list[str]) -> None:
    app = app_context.get()
    book_page = app["book"]
    logger = app["logger"]
    thresholds = app["config"]["performance_thresholds"]
    
    for url in book_urls:
        label = url.split('/')[-1]
        await book_page.measure_page_performance(
            url, 
            thresholds["book_page"], 
            f"Load Book: {label}"
        )

        # Randomize target list for diverse test coverage
        target_status = random.choice(["Want to Read", "Already Read"])
        logger.info(f"Adding {url} to {target_status}")
        
        success = await book_page.add_to_list_specific(target_status)
        if success != "Failed":
            book_slug = url.split('/')[-1].split('?')[0]
            
            # Evidence collection: Capture and attach screenshot to Allure
            screenshot_path = await capture_book_addition(book_slug, book_page.page, logger)
            allure.attach.file(
                screenshot_path, 
                name=f"Added: {book_slug}", 
                attachment_type=allure.attachment_type.PNG
            )
            logger.info(f"Visual evidence attached to Allure for '{book_slug}'")

@allure.step("Workflow: Verify Reading List Sync")
async def assert_reading_list_count(expected_count: int):
    app = app_context.get()
    reading_page = app["reading_list"]
    
    max_retries = 10
    
    for attempt in range(max_retries):
        # Technical retrieval of current aggregate count
        actual_total = await reading_page.get_total_reading_list_count()
        
        if actual_total == expected_count:
            return  # Success: exit the sync loop
            
        # Recovery Strategy: Reload page periodically to force server sync
        if attempt > 0 and attempt % 3 == 0:
            await reading_page.page.reload()
            
        await asyncio.sleep(1)

    # Final assertion after all retry attempts are exhausted
    actual_final = await reading_page.get_total_reading_list_count()
    assert actual_final == expected_count, f"Sync failed: Expected {expected_count}, got {actual_final}"

@allure.step("Workflow: Full Environment Cleanup")
async def clear_all_reading_lists(user_name: str):
    app = app_context.get()
    reading_page = app["reading_list"]
    
    # Define mapping of lists that require cleanup
    list_map = {"want-to-read": "Want to Read", "already-read": "Already Read"}

    for list_id, btn_text in list_map.items():
        await reading_page.navigate_to_specific_list(user_name, list_id)
        
        # Iteratively remove items until the list is empty
        max_attempts = 20
        for _ in range(max_attempts):
            current_count = await reading_page.get_active_toggle_count(btn_text)
            if current_count == 0:
                break
                
            try:
                await reading_page.remove_first_item_from_list(btn_text)
            except Exception:
                # Recovery: Reload and re-navigate if an interaction is interrupted
                await reading_page.page.reload()
                await reading_page.navigate_to_specific_list(user_name, list_id)