import re
import logging
from playwright.async_api import expect, Page
from .base_page import BasePage

class SearchPage(BasePage):
    """
    Handles interactions with the Open Library search results page.
    Utilizes resilient Locators and efficient filtering for high-performance automation.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)
    
    SEARCH_INPUT = "input[name='q'], input[aria-label='Search']"
    RESULT_ITEMS = ".searchResultItem"
    BOOK_TITLE_LINK = "h3.booktitle > a"
    PUBLICATION_YEAR_DETAILS = ".resultDetails"
    PUBLICATION_YEAR_EDITIONS = ".bookEditions"
    NEXT_PAGE_SELECTOR = "a.pagination-item.pagination-arrow[aria-label='Go to next page']"

    async def execute_search(self, query: str):
        """
        Executes search and waits for content visibility using built-in assertions.
        """
        input_field = self.page.locator(self.SEARCH_INPUT)
        await expect(input_field).to_be_visible(timeout=10000)
        
        await input_field.fill(query)
        await self.page.keyboard.press("Enter")
        
        # Ensure results are populated before continuing
        await expect(self.page.locator(self.RESULT_ITEMS).first).to_be_visible(timeout=15000)

    async def get_filtered_books(self, max_year: int, limit: int):
        """
        Main orchestration: iterates through result pages until the limit is met.
        """
        found_books = []
        current_page = 1
       
        while len(found_books) < limit:
            self.logger.info(f"Scanning results on page {current_page}...")
            
            # Extract matches from current page
            page_matches = await self._parse_results_on_page(max_year, limit - len(found_books))
            found_books.extend(page_matches)
            
            if len(found_books) >= limit:
                break

            current_page += 1
            if not await self._navigate_to_page():
                break

        return found_books

    async def _parse_results_on_page(self, max_year: int, remaining_limit: int):
        """
        Parses results using the Locator API for stability.
        """
        matches = []
        results = await self.page.locator(self.RESULT_ITEMS).all()

        domain = self.config['urls']['base_url'].rstrip('/')

        for item in results:
            if len(matches) >= remaining_limit:
                break

            year_element = item.locator(self.PUBLICATION_YEAR_DETAILS)
            if await year_element.count() == 0:
                year_element = item.locator(self.PUBLICATION_YEAR_EDITIONS)

            year_text = await year_element.first.inner_text()
            year = self._extract_year(year_text)
            
            if year and year <= max_year:
                link_locator = item.locator(self.BOOK_TITLE_LINK)
                if await link_locator.count() > 0:
                    href = await link_locator.get_attribute("href")
                    if not href:
                        self.logger.warning("Link found but href attribute is missing. Skipping.")
                        continue

                    full_url = f"{domain}{href}"
                    matches.append(full_url)
                    self.logger.info(f"Match found ({year}): {full_url}")
                    
        return matches

    async def _navigate_to_page(self) -> bool:
        """
        Handles sequential pagination by interacting with the 'Next' control.
        Ensures a stable state transition before returning execution to the caller.
        """
        # Locate the specific 'Next' link using the data-attribute selector
        next_button = self.page.locator(self.NEXT_PAGE_SELECTOR)
        
        # Check for existence to prevent unnecessary exceptions at the end of the result set
        if await next_button.count() == 0:
            self.logger.info("Pagination: No 'Next' button detected. Result set exhausted.")
            return False

        try:
            # Capture current URL to verify transition
            current_url = self.page.url
            
            self.logger.info(f"Initiating transition to the next results page.")
            await next_button.click()

            # Wait for the URL to change - a very reliable indicator in OpenLibrary
            await self.page.wait_for_function(f"() => window.location.href !== '{current_url}'")
            
            # Ensure the new results are rendered
            await expect(self.page.locator(self.RESULT_ITEMS).first).to_be_visible(timeout=10000)
            
            return True
        except Exception as e:
            self.logger.warning(f"Pagination navigation failed or timed out: {str(e)}")
            return False

    def _extract_year(self, text: str):
        match = re.search(r'\d{4}', text)
        return int(match.group()) if match else None