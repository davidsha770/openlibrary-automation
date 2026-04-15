import re
from .base_page import BasePage

class ReadingListPage(BasePage):
    """
    Page Object for the Reading List pages.
    Handles sidebar count verification and automated cleanup of reading lists.
    """
    # Dynamic selector using a template for different list tracking IDs
    SIDEBAR_COUNT_SPAN = "a[data-ol-link-track='MyBooksSidebar|{list_id}'] span.li-count"
    LIST_URL_TEMPLATE = "https://openlibrary.org/people/{user_name}/books/{list_type}"

    async def get_sidebar_count(self, list_id: str) -> int:
        """
        Extracts the numeric count from the sidebar for a specific list.
        list_id: 'WantToRead' or 'AlreadyRead' (based on site tracking data).
        """
        try:
            selector = self.SIDEBAR_COUNT_SPAN.format(list_id=list_id)
            element = self.page.locator(selector)
            
            # Explicit wait for the sidebar component to hydrate and become visible
            await element.wait_for(state="visible", timeout=5000)
            
            text = await element.inner_text()
            self.logger.info(f"Sidebar {list_id} raw text captured: '{text}'")
            
            # Use Regex to extract only digits from the captured text (e.g., "(5)" -> 5)
            match = re.search(r'\d+', text)
            return int(match.group()) if match else 0
        except Exception as e:
            self.logger.warning(f"Could not retrieve sidebar count for {list_id}: {e}")
            return 0

    async def assert_reading_list_count(self, expected_count: int):
        """
        Orchestrates the final verification by navigating to 'My Books' 
        and aggregating counts from both 'Want to Read' and 'Already Read' lists.
        """
        # 1. Navigate to the main books account page to ensure the sidebar is refreshed
        self.logger.info("Navigating to My Books to verify final counts...")
        await self.page.goto("https://openlibrary.org/account/books", wait_until="networkidle")
        
        # 2. Retrieve counts using tracking IDs
        want_count = await self.get_sidebar_count("WantToRead")
        read_count = await self.get_sidebar_count("AlreadyRead")
        
        total = want_count + read_count
        self.logger.info(f"Final Assertion: Sidebar combined total is {total} (Expected: {expected_count})")
        
        # 3. Assert match and capture evidence on failure
        if total != expected_count:
            await self.page.screenshot(path="outputs/sidebar_mismatch.png")
            raise AssertionError(f"Count mismatch! Sidebar total is {total}, but expected {expected_count}")
        
        self.logger.info("✅ SUCCESS: Reading list counts match the expected value!")

    async def clear_reading_lists(self, user_name: str):
        """
        Bulk cleanup: Removes all books from the user's lists by toggling the active status buttons.
        This ensures a clean test environment for subsequent executions.
        """
        # Map internal list identifiers to the button text present on the UI
        list_map = {
            "want-to-read": "Want to Read",
            "already-read": "Already Read"
        }

        for list_id, btn_text in list_map.items():
            target_url = self.LIST_URL_TEMPLATE.format(user_name=user_name, list_type=list_id)
            
            # Standard navigation to the specific list page
            await self.page.goto(target_url, wait_until="load")
            
            # Locate all buttons that represent an 'active' status for the current list
            active_buttons = await self.page.locator(f"button:has-text('{btn_text}')").all()

            if not active_buttons:
                self.logger.info(f"List '{list_id}' is already clean/empty.")
                continue

            self.logger.info(f"Detected {len(active_buttons)} books to remove from '{list_id}'")

            for btn in active_buttons:
                try:
                    # Defensive check: ensure button is still in viewport before clicking
                    if await btn.is_visible():
                        await btn.click()
                        # Brief stabilization delay to allow AJAX request processing
                        await self.page.wait_for_timeout(800) 
                except Exception as e:
                    self.logger.error(f"Failed to remove book via button '{btn_text}': {e}")