import re
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
    NEXT_PAGE_BTN = "a.next-page, a.next"

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

    async def get_filtered_books(self, max_year: int, limit: int):
        """
        Scans search results (including pagination) and returns books published before max_year.
        This method encapsulates all the DOM-traversal logic.
        """
        found_books = []
        base_url = "https://openlibrary.org"

        while len(found_books) < limit:
            # Get current results on the page
            results = await self.page.query_selector_all(self.RESULT_ITEMS)
            
            for item in results:
                if len(found_books) >= limit:
                    break
                
                # Extract publication year
                year_el = await item.query_selector(self.PUBLICATION_YEAR_TEXT)
                if year_el:
                    year_text = await year_el.inner_text()
                    year = await self.extract_year_from_text(year_text)
                    
                    # Filter logic
                    if year and year < max_year:
                        link_el = await item.query_selector(self.BOOK_TITLE_LINK)
                        if link_el:
                            title = await link_el.inner_text()
                            href = await link_el.get_attribute("href")
                            found_books.append({
                                "title": title.strip(),
                                "url": base_url + href,
                                "year": year
                            })
                            self.logger.info(f"Match found: {title.strip()} ({year})")
            
            # Pagination logic: Go to next page if we haven't reached the limit
            if len(found_books) < limit:
                next_btn = await self.page.query_selector(self.NEXT_PAGE_BTN)
                if next_btn:
                    await next_btn.click()
                    await self.page.wait_for_load_state("networkidle")
                else:
                    self.logger.info("No more pages available.")
                    break
                    
        return found_books

    async def go_to_next_page(self):
        """
        Simple wrapper for clicking the next page.
        """
        next_btn = await self.page.query_selector(self.NEXT_PAGE_BTN)
        if next_btn:
            await next_btn.click()
            await self.page.wait_for_load_state("networkidle")
            return True
        return False