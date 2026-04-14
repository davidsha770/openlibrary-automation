import re
import os
from .base_page import BasePage

class SearchPage(BasePage):
    """
    Handles interactions with the Open Library search results page.
    Provides methods for searching, result filtering, and pagination.
    """
    # Centralized selectors for maintenance
    SEARCH_INPUT = "input[name='q'], input[aria-label='Search']"
    RESULT_ITEMS = ".searchResultItem"
    BOOK_TITLE_LINK = "h3.booktitle a.results, .result-item-title a"
    PUBLICATION_YEAR_TEXT = ".resultDetails, .bookEditions"
    # Targeted selector for the SVG icon within the pagination link
    NEXT_PAGE_BTN = "a:has(svg path[d='m9 18 6-6-6-6']), a.nextPagination, a[rel='next']"

    async def execute_search(self, query: str):
        """
        Inputs the search query and submits the search.
        """
        await self.page.wait_for_selector(self.SEARCH_INPUT, state="visible", timeout=10000)
        await self.page.fill(self.SEARCH_INPUT, query)
        await self.page.keyboard.press("Enter")
        
        try:
            await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=15000)
        except Exception:
            self.logger.warning(f"Timeout: Search results for '{query}' did not appear.")

    async def extract_year_from_text(self, text: str):
        """
        Extracts a 4-digit year from metadata strings using Regex.
        """
        match = re.search(r'\d{4}', text)
        return int(match.group()) if match else None

    async def get_filtered_books(self, base_url: str, max_year: int, limit: int):
        """
        Iterates through search results across multiple pages until the limit is reached
        or no more pages are available. Filters books by publication year.
        """
        found_books = []
        
        while len(found_books) < limit:
            # Wait for results to be present in the DOM
            await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=10000)
            results = await self.page.query_selector_all(self.RESULT_ITEMS)
            
            for item in results:
                if len(found_books) >= limit:
                    return found_books

                year_el = await item.query_selector(self.PUBLICATION_YEAR_TEXT)
                if year_el:
                    year_text = await year_el.inner_text()
                    year = await self.extract_year_from_text(year_text)
                    
                    if year and year <= max_year:
                        link_el = await item.query_selector(self.BOOK_TITLE_LINK)
                        if link_el:
                            href = await link_el.get_attribute("href")
                            full_url = base_url + href
                            found_books.append(full_url)
                            self.logger.info(f"Match {len(found_books)}: {full_url}")

            # Pagination Logic
            self.logger.info("Searching for next page button (SVG hunter)...")
            next_btn = self.page.locator(self.NEXT_PAGE_BTN).first
            
            if await next_btn.is_visible():
                self.logger.info("SVG Next button found. Navigating to next page...")
                current_url = self.page.url
                await next_btn.click()
                
                # Wait for the URL to change and new results to load
                try:
                    await self.page.wait_for_function(f"() => window.location.href !== '{current_url}'", timeout=5000)
                    await self.page.wait_for_selector(self.RESULT_ITEMS, timeout=10000)
                except Exception as e:
                    self.logger.warning(f"Pagination sync issue: {e}. Proceeding with manual timeout.")
                    await self.page.wait_for_timeout(2000)
            else:
                self.logger.warning("No more pages available.")
                break

        return found_books

    async def go_to_next_page(self):
        """
        Navigates to the next page of results.
        """
        next_btn = self.page.locator(self.NEXT_PAGE_BTN).first
        if await next_btn.is_visible():
            await next_btn.click()
            await self.page.wait_for_load_state("load")
            return True
        return False
    
    async def dump_page_html(self, filename="search_debug.html"):
        """
        Saves the current page HTML to a file for debugging purposes.
        """
        os.makedirs("outputs", exist_ok=True)
        content = await self.page.content()
        file_path = os.path.join("outputs", filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"--- FULL HTML DUMP SAVED TO: {file_path} ---")