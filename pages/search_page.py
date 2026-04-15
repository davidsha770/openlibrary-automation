import re
import os
from .base_page import BasePage

class SearchPage(BasePage):
    """
    Handles interactions with the Open Library search results page.
    Includes optimized pagination and result filtering logic based on publication years.
    """
    
    # Centralized selectors for easy maintenance and robustness
    SEARCH_INPUT = "input[name='q'], input[aria-label='Search']"
    RESULT_ITEMS = ".searchResultItem"
    BOOK_TITLE_LINK = "h3.booktitle > a"
    # Selectors for extracting metadata like publication date
    PUBLICATION_YEAR_TEXT = ".resultDetails, .bookEditions"

    async def execute_search(self, query: str):
        """
        Inputs the search query and submits the search using the keyboard.
        Waits for result items to appear to ensure the search was successful.
        """
        await self.page.wait_for_selector(self.SEARCH_INPUT, state="visible", timeout=10000)
        await self.page.fill(self.SEARCH_INPUT, query)
        await self.page.keyboard.press("Enter")
        
        try:
            # Explicit wait for at least one result item to load
            await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=15000)
        except Exception:
            self.logger.warning(f"Timeout: Search results for '{query}' did not appear.")

    async def get_filtered_books(self, base_url: str, max_year: int, limit: int):
        """
        Main orchestration method: iterates through multiple result pages 
        to collect books matching the year criteria until the requested limit is met.
        """
        found_books = []
        current_page = 1
        
        while len(found_books) < limit:
            self.logger.info(f"Scanning results on page {current_page}...")
            
            # 1. Parse current page results and collect matches
            page_matches = await self._parse_results_on_page(base_url, max_year, limit - len(found_books))
            found_books.extend(page_matches)
            
            # Exit loop if limit reached
            if len(found_books) >= limit:
                break

            # 2. Handle Pagination: attempt to navigate to the next result page
            current_page += 1
            navigation_success = await self._navigate_to_page(current_page)
            if not navigation_success:
                # Break if no further pages are available
                break

        return found_books

    async def _parse_results_on_page(self, base_url: str, max_year: int, remaining_limit: int):
        """
        Helper method to iterate over book items on the current page.
        Filters books based on the first identified year in the metadata text.
        """
        matches = []
        await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=10000)
        results = await self.page.query_selector_all(self.RESULT_ITEMS)

        for item in results:
            if len(matches) >= remaining_limit:
                break

            # Extract publication info text
            year_el = await item.query_selector(self.PUBLICATION_YEAR_TEXT)
            if not year_el:
                continue

            year_text = await year_el.inner_text()
            year = self._extract_year(year_text)
            
            # Filter condition: year must be less than or equal to max_year
            if year and year <= max_year:
                link_el = await item.query_selector(self.BOOK_TITLE_LINK)
                if link_el:
                    href = await link_el.get_attribute("href")
                    full_url = base_url + href
                    matches.append(full_url)
                    self.logger.info(f"Match {len(matches)}: {full_url}")
        return matches

    async def _navigate_to_page(self, page_num: int):
        """
        Handles complex pagination by targeting ARIA labels and text content.
        Uses a fallback selector strategy for high reliability.
        """
        self.logger.info(f"Attempting to navigate to page {page_num}...")
        
        # Primary: Aria-label for accessibility; Fallback: exact text match within pagination links
        selector = f"a[aria-label='Go to page {page_num}'], a.pagination-item:has-text('{page_num}')"
        
        try:
            btn = await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            await btn.click()
            
            # Wait for both network stability and a fixed timeout to allow content hydration
            await self.page.wait_for_load_state("load")
            await self.page.wait_for_timeout(2000) 
            return True
        except Exception:
            self.logger.warning(f"Page {page_num} not found or unreachable. Ending search traversal.")
            return False

    def _extract_year(self, text: str):
        """
        Utility to extract a 4-digit year from a string using Regex.
        Returns the first match found or None if no year is detected.
        """
        match = re.search(r'\d{4}', text)
        return int(match.group()) if match else None

    async def dump_page_html(self, filename="search_debug.html"):
        """
        Saves current page HTML to the outputs directory for debugging purposes.
        Useful for analyzing DOM structure during failures.
        """
        os.makedirs("outputs", exist_ok=True)
        content = await self.page.content()
        file_path = os.path.join("outputs", filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        self.logger.info(f"HTML debug dump saved to: {file_path}")