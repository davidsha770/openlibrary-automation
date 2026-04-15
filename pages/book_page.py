import os
import allure
from .base_page import BasePage

class BookPage(BasePage):
    """
    Handles book-specific interactions on the Open Library book detail page.
    """

    # --- Locators ---
    # Main button for 'Want to Read'
    WANT_TO_READ_BTN = "button:has-text('Want to Read')"
    # The arrow/trigger to open the lists dropdown
    DROPDOWN_TRIGGER = "a.generic-dropper__dropclick"
    # The specific button inside the dropdown for 'Already Read'
    ALREADY_READ_BTN = "button.nostyle-btn"
    # Container for dropdown options to ensure visibility
    DROPDOWN_MENU = ".results, .dropdown-menu"

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
            await primary_btn.wait_for(state="attached", timeout=15000)

            if status == "Already Read":
                # 1. Open the dropdown menu
                trigger = self.page.locator(self.DROPDOWN_TRIGGER).first
                await trigger.wait_for(state="visible", timeout=5000)
                await trigger.click()
                
                # 2. Select 'Already Read' from the opened menu
                # Using exact=True to avoid partial matches with other list names
                option = self.page.locator(self.ALREADY_READ_BTN).get_by_text("Already Read", exact=True).first
                await option.wait_for(state="visible", timeout=5000)
                await option.click()
            else:
                # Direct click for the default 'Want to Read' action
                await primary_btn.click()

            # Ensure the request is processed before moving on
            await self.page.wait_for_load_state("networkidle")
            self.logger.info(f"Successfully added book as: {status}")
            return status

        except Exception as e:
            self.logger.error(f"Failed to add book to list '{status}': {e}")
            # Capture error state for debugging
            await self.page.screenshot(path=f"outputs/error_book_{status}.png")
            return "Failed"
        
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

        allure.attach.file(
            screenshot_path, 
            name=f"Screenshot: {book_title}", 
            attachment_type=allure.attachment_type.PNG
        )
        self.logger.info(f"Visual evidence attached to Allure for '{book_title}'")