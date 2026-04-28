import os
import logging
from playwright.async_api import Page, expect
from .base_page import BasePage
from utils.decorators import retry_on_failure

class BookPage(BasePage):
    """
    Handles book-specific interactions on the Open Library book detail page.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)

    # --- Locators ---
    # Main button for 'Want to Read'
    WANT_TO_READ_BTN = "button:has-text('Want to Read')"
    # The arrow/trigger to open the lists dropdown
    DROPDOWN_TRIGGER = "a.generic-dropper__dropclick"
    # The specific button inside the dropdown for 'Already Read'
    ALREADY_READ_BTN = "button[data-track='AlreadyRead'], button:has-text('Already Read')"

    @retry_on_failure(times=2, delay=2)
    async def add_to_list_specific(self, status: str) -> str:
        """
        Adds a book to a specific reading list (Want to Read or Already Read).
        
        Args:
            status (str): The target list name ('Want to Read' or 'Already Read').
            
        Returns:
            str: The status if successful, "Failed" otherwise.
        """
        try:
            # Locate the primary button to ensure page is loaded
            primary_btn = self.page.locator(self.WANT_TO_READ_BTN).first
            await primary_btn.wait_for(state="visible", timeout=15000)

            if status == "Already Read":
                # 1. Open the dropdown menu
                trigger = self.page.locator(self.DROPDOWN_TRIGGER).first
                await trigger.click()

                # 2. Click the option
                option = self.page.locator(self.ALREADY_READ_BTN).first
                await option.wait_for(state="visible", timeout=5000)
                await option.click()
                
                success_indicator = self.page.locator(f"button.book-progress-btn.activated:has-text('{status}')")
            else:
                # Direct click for the default 'Want to Read' action
                await primary_btn.click()
                success_indicator = self.page.locator("button.book-progress-btn.activated:has-text('Want to Read')")

            await expect(success_indicator.first).to_be_visible(timeout=10000)
            
            # Final sync to ensure DB/API update is reflected
            await self.page.wait_for_load_state("networkidle") 
            
            self.logger.info(f"State change verified: Book is now '{status}'")
            return status

        except Exception as e:
            await self.report_error(e, f"Failed to add book to '{status}'", f"error_book_{status}")
            raise e
        
    async def capture_book_addition(self, book_title: str):
        """
        Captures a visual confirmation screenshot.
        Sanitizes the book title to create a valid filesystem filename.
        """
        screenshot_dir = os.path.join("outputs", "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Replace non-alphanumeric characters with underscores for safe filenames
        safe_name = "".join([c if c.isalnum() else "_" for c in book_title])[:50]
        screenshot_path = os.path.join(screenshot_dir, f"{safe_name}.png")
        
        await self.page.screenshot(path=screenshot_path)
        self.logger.info(f"Visual evidence captured for '{book_title}' at {screenshot_path}")
        return screenshot_path
