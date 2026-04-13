import re
from .base_page import BasePage

class SearchPage(BasePage):
    """
    Handles interactions with the Open Library search results page.
    Provides methods for searching, result filtering, and pagination.
    """
    # Flexible selectors to handle various Open Library UI versions
    SEARCH_INPUT = "input[name='q'], input[aria-label='Search']"
    RESULT_ITEMS = ".searchResultItem"
    BOOK_TITLE_LINK = "h3.booktitle a.results, .result-item-title a"
    PUBLICATION_YEAR_TEXT = ".resultDetails, .bookEditions"
    NEXT_PAGE_BTN = "a.next-page, a.next"

    async def execute_search(self, query: str):
        """
        Inputs the search query and submits by pressing Enter.
        This approach bypasses inconsistent search button selectors.
        """
        # Ensure the search field is interactive before typing
        await self.page.wait_for_selector(self.SEARCH_INPUT, state="visible", timeout=10000)
        await self.page.fill(self.SEARCH_INPUT, query)
        
        # Simulate Enter key to trigger search submission
        await self.page.keyboard.press("Enter")
        
        # Allow time for results to populate the DOM
        try:
            await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=15000)
        except Exception:
            self.logger.warning(f"Timeout: Search results for '{query}' did not appear.")

    async def extract_year_from_text(self, text: str):
        """
        Extracts a 4-digit year from metadata strings using Regex.
        Example: 'First published in 1965' -> 1965.
        """
        match = re.search(r'\d{4}', text)
        return int(match.group()) if match else None

    async def get_results_on_page(self):
        """
        Retrieves all individual search result elements currently displayed.
        """
        return await self.page.query_selector_all(self.RESULT_ITEMS)

    async def go_to_next_page(self):
        """
        Attempts to click the next page button if available.
        Returns True if navigation was successful, False otherwise.
        """
        next_btn = await self.page.query_selector(self.NEXT_PAGE_BTN)
        if next_btn:
            await next_btn.click()
            # Wait for network activity to settle before returning control
            await self.page.wait_for_load_state("networkidle")
            return True
        return False