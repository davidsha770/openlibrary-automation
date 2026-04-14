from pages.base_page import BasePage

class ReadingListPage(BasePage):
    """
    Page Object for the Reading List pages (Want to Read, Already Read, etc.)
    """
    
    # --- Selectors ---
    # Centralizing selectors here allows us to update them in one place if the site changes
    BOOK_TITLES = "h3.booktitle a"
    LIST_URL_TEMPLATE = "https://openlibrary.org/people/user532228/books/{list_type}"

    async def get_all_book_titles(self, list_type: str, threshold: int):
        """
        Navigates to a specific reading list, measures performance, 
        and extracts all book titles.
        
        :param list_type: The type of list to fetch (e.g., 'want-to-read' or 'already-read')
        :param threshold: Performance budget in milliseconds
        :return: A list of normalized book titles (lowercase and stripped)
        """
        # Construct the URL based on the list type
        target_url = self.LIST_URL_TEMPLATE.format(list_type=list_type)
        
        # 1. Navigation & Performance Measurement
        # We use the method from BasePage to handle both the goto and the metric collection
        await self.measure_page_performance(
            target_url, 
            threshold, 
            f"Verify List: {list_type}"
        )
        
        self.logger.info(f"Successfully navigated to {list_type} list.")

        # 2. Smart Waiting
        # Instead of a hard sleep, we wait for the book titles to appear in the DOM.
        # This makes the test faster and more stable.
        try:
            await self.page.wait_for_selector(self.BOOK_TITLES, timeout=10000)
        except Exception:
            self.logger.warning(f"No books found or page took too long to hydrate for: {list_type}")
            return []

        # 3. Data Extraction
        # locator().all_inner_texts() is the modern Playwright way to get a list of strings
        titles = await self.page.locator(self.BOOK_TITLES).all_inner_texts()
        
        # 4. Normalization
        # Returning clean data ensures the E2E script can perform reliable comparisons (assertions)
        normalized_titles = [t.lower().strip() for t in titles]
        
        self.logger.info(f"Retrieved {len(normalized_titles)} titles from {list_type}.")
        return normalized_titles

    async def is_book_in_list(self, book_title: str, list_type: str, threshold: int) -> bool:
        """
        Helper method to check if a specific book exists in a specific list.
        """
        titles = await self.get_all_book_titles(list_type, threshold)
        return book_title.lower().strip() in titles