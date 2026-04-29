from contextvars import ContextVar
import allure
import random

# Registry גלובלי שיאותחל על ידי ה-Test Fixture
app_context: ContextVar[dict] = ContextVar("app_context")

@allure.step("Spec Flow: search_books_by_title_under_year")
async def search_books_by_title_under_year(query: str, max_year: int, limit: int = 5) -> list[str]:
    app = app_context.get()

    search_page = app["search"]
    urls = app["config"]["urls"]
    thresholds = app["config"]["performance_thresholds"]

    await search_page.measure_page_performance(
        urls["base_url"], 
        thresholds["search_page"], 
        "Search Page Load"
    )
    await search_page.execute_search(query)
    return await search_page.get_filtered_books(max_year, limit)

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

        target_status = random.choice(["Want to Read", "Already Read"])
        logger.info(f"Adding {url} to {target_status}")
        
        success = await book_page.add_to_list_specific(target_status)
        if success != "Failed":
            book_slug = url.split('/')[-1].split('?')[0]
            screenshot_path = await book_page.capture_book_addition(book_slug)
            allure.attach.file(screenshot_path, name=f"Added: {book_slug}", attachment_type=allure.attachment_type.PNG)
            logger.info(f"Visual evidence attached to Allure for '{book_slug}'")

@allure.step("Spec Flow: assert_reading_list_count")
async def assert_reading_list_count(expected_count: int) -> None:
    app = app_context.get()

    reading_list_page = app["reading_list"]
    display_name = app["config"]["auth"]["display_name"]
    urls = app["config"]["urls"]
    thresholds = app["config"]["performance_thresholds"]

    list_url = f"{urls['base_url']}/people/{display_name}/books"
    await reading_list_page.measure_page_performance(list_url, thresholds["reading_list"], "Reading List Load")
    await reading_list_page.assert_reading_list_count(expected_count)