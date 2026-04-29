import re
from playwright.async_api import expect, Page
import logging
import asyncio
from .base_page import BasePage

class ReadingListPage(BasePage):
    """
    Page Object for the Reading List pages.
    Handles sidebar count verification and automated cleanup of reading lists.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)
    # Dynamic selector using a template for different list tracking IDs
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
            
            # Ensure the sidebar element is visible and populated
            await expect(element).to_be_visible(timeout=5000)
            
            text = await element.inner_text()
            self.logger.info(f"Sidebar {list_id} raw text captured: '{text}'")
            
            # Use Regex to extract only digits from the captured text (e.g., "(5)" -> 5)
            match = re.search(r'\d+', text)
            return int(match.group()) if match else 0
        except Exception as e:
            await self.report_error(e, f"Failed to retrieve sidebar count for {list_id}", level="warning")
            return 0
        
    async def get_aggregate_count(self) -> int:
        """Helper to sum both lists."""
        want_count = await self.get_sidebar_count("WantToRead")
        read_count = await self.get_sidebar_count("AlreadyRead")
        return want_count + read_count

    async def assert_reading_list_count(self, expected_count: int):
        """
        Verifies that the aggregate count of all reading lists matches expectations.
        Ensures proper navigation and URL validation before assertion.
        """
        self.logger.info("Navigating to 'My Books' for final count verification.")
        
        # Explicit navigation if the current URL does not match the target
        target_url = f"{self.config['urls']['base_url'].rstrip('/')}{self.MY_BOOKS_PATH}"
        if self.page.url != target_url:
            await self.page.goto(target_url, wait_until="domcontentloaded")
        
        # Validate that we are indeed on the books management page
        await expect(self.page).to_have_url(re.compile(r".*/books.*"))

        max_retries = 10
        actual_total = 0
        
        for attempt in range(max_retries):
            actual_total = await self.get_aggregate_count()
            if actual_total == expected_count:
                self.logger.info(f"Success: Count reached {expected_count} after {attempt} retries.")
                return
            
            if attempt > 0 and attempt % 3 == 0:
                self.logger.debug(f"Attempt {attempt}: Syncing with server via page reload...")
                await self.page.reload(wait_until="domcontentloaded")
        
            self.logger.debug(f"Attempt {attempt+1}: Count is {actual_total}, waiting for {expected_count}...")
            await asyncio.sleep(1)
        
        if actual_total != expected_count:
            await self.report_error(
                AssertionError(f"Expected {expected_count}, got {actual_total}"), 
                "Final count verification failed", 
                "sidebar_mismatch"
            )
            raise AssertionError(f"Count mismatch: Sidebar total is {actual_total}, expected {expected_count}")
        
        self.logger.info("Verification Successful: Reading list counts match.")

    async def clear_reading_lists(self, user_name: str):
        """
        Iterates through reading lists and removes all items to ensure a clean state.
        Uses a dynamic wait strategy to optimize speed and prevents infinite loops.
        """
        list_map = {"want-to-read": "Want to Read", "already-read": "Already Read"}

        for list_id, btn_text in list_map.items():
            path = self.LIST_PATH_TEMPLATE.format(user_name=user_name, list_type=list_id)
            target_url = f"{self.config['urls']['base_url'].rstrip('/')}{path}"
            await self.page.goto(target_url, wait_until="domcontentloaded")
            
            # Target buttons that represent an active state for the current list
            selector = self.ACTIVE_STATUS_BTN_TEMPLATE.format(btn_text)
            active_toggles = self.page.locator(selector)

            try:
                await active_toggles.first.wait_for(state="visible", timeout=5000)
            except Exception as e:
                self.logger.debug(f"List {list_id} check finished: {e}")
                self.logger.info(f"List {list_id} is empty, skipping cleanup.")
                continue
            
            # Safety limit to prevent infinite loops in CI environments
            max_cleanup_attempts = 20
            attempts = 0
            
            while attempts < max_cleanup_attempts:
                count = await active_toggles.count()
                if count == 0:
                    break

                attempts += 1
                try:
                    await active_toggles.first.click()
                    await expect(active_toggles).to_have_count(count - 1, timeout=5000)

                except Exception as e:
                    # Specific recovery logic: reload and re-locate elements
                    await self.report_error(e, f"Interruption during cleanup of {list_id}", level="debug")
                    await self.page.reload(wait_until="domcontentloaded")
                    # Re-bind the locator after reload to avoid 'Stale Element' issues
                    selector = self.ACTIVE_STATUS_BTN_TEMPLATE.format(btn_text)
                    active_toggles = self.page.locator(selector)