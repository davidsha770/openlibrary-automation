import re
from playwright.async_api import expect, Page
import logging
from .base_page import BasePage

class ReadingListPage(BasePage):
    """
    Page Object for the Reading List pages.
    Handles technical interactions, data extraction, and navigation for user books.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)

    # --- Selectors ---
    # Dynamic selector template for list tracking IDs in the sidebar
    SIDEBAR_COUNT_SPAN = "a[data-ol-link-track='MyBooksSidebar|{list_id}'] span.li-count"
    LIST_PATH_TEMPLATE = "/people/{user_name}/books/{list_type}"
    MY_BOOKS_PATH = "/account/books"
    ACTIVE_STATUS_BTN_TEMPLATE = "button.book-progress-btn.activated:has-text('{0}')"

    async def get_sidebar_count(self, list_id: str) -> int:
        """
        Extracts the numeric count from the sidebar for a specific list.
        
        Args:
            list_id: 'WantToRead' or 'AlreadyRead' based on site tracking attributes.
        Returns:
            The integer count found in the sidebar, or 0 if retrieval fails.
        """
        try:
            selector = self.SIDEBAR_COUNT_SPAN.format(list_id=list_id)
            element = self.page.locator(selector)

            if await element.count() == 0:
                return 0
            
            # Ensure the sidebar element is visible and populated before extraction
            await expect(element).to_be_visible(timeout=5000)
            
            text = await element.inner_text()
            self.logger.info(f"Sidebar {list_id} raw text captured: '{text}'")
            
            # Extract digits using Regex (e.g., handles formats like "(5)" or "5 items")
            match = re.search(r'\d+', text)
            return int(match.group()) if match else 0
        except Exception as e:
            await self.report_error(e, f"Technical failure retrieving sidebar count for {list_id}", level="warning")
            return 0
        
    async def get_aggregate_count(self) -> int:
        """Technical Utility: Sums the counts of both primary reading lists."""
        want_count = await self.get_sidebar_count("WantToRead")
        read_count = await self.get_sidebar_count("AlreadyRead")
        return want_count + read_count

    async def get_total_reading_list_count(self) -> int:
        """
        Technical Action: Navigates to the Books Overview and retrieves the aggregate count.
        No business logic or retry loops are implemented here.
        """      
        target_url = f"{self.config['urls']['base_url'].rstrip('/')}{self.MY_BOOKS_PATH}"
        if self.page.url != target_url:
            await self.page.goto(target_url, wait_until="domcontentloaded")
        
        # Verify page state before data extraction
        await expect(self.page).to_have_url(re.compile(r".*/books.*"))
        return await self.get_aggregate_count()

    async def navigate_to_specific_list(self, user_name: str, list_type: str):
        """Technical Action: Performs direct navigation to a specific sub-list."""
        path = self.LIST_PATH_TEMPLATE.format(user_name=user_name, list_type=list_type)
        target_url = f"{self.config['urls']['base_url'].rstrip('/')}{path}"
        await self.page.goto(target_url, wait_until="domcontentloaded")

    async def get_active_toggle_count(self, list_name_text: str) -> int:
        """Technical Utility: Returns the number of active list-status buttons on the page."""
        selector = self.ACTIVE_STATUS_BTN_TEMPLATE.format(list_name_text)
        return await self.page.locator(selector).count()

    async def remove_first_item_from_list(self, list_name_text: str):
        """
        Technical Action: Clicks the first active removal button.
        Uses a technical assertion to ensure UI stability before returning control.
        """
        selector = self.ACTIVE_STATUS_BTN_TEMPLATE.format(list_name_text)
        active_toggles = self.page.locator(selector)
        
        count_before = await active_toggles.count()
        if count_before > 0:
            await active_toggles.first.click()
            # Technical wait: ensuring the DOM reflects the change before the next operation
            await expect(active_toggles).to_have_count(count_before - 1, timeout=5000)