from .base_page import BasePage

class ReadingListPage(BasePage):
    """
    Handles interactions with the user's reading lists (e.g., Want to Read, Already Read).
    Deals with Web Components and asynchronous content hydration.
    """
    # Base selectors for identifying list items and titles
    LIST_ITEM_SELECTOR = ".listbook-item, .list-books .book-item"
    BOOK_TITLE_SELECTOR = ".book-title, .result-item-title a"

    async def get_all_book_titles(self) -> list:
        """
        Retrieves all book titles from the current reading list page.
        Includes a wait for Web Component hydration to ensure data is visible.
        """
        self.logger.info("Waiting for Web Components to hydrate...")
        
        # Open Library often uses custom elements (Shadow DOM) for list items.
        # We wait for these specific tags or fallback list items.
        try:
            await self.page.wait_for_selector("ol-read-more, .list-item, .book-item", timeout=15000)
        except Exception:
            self.logger.warning("Web Components hydration timed out. Attempting to scrape remaining DOM.")

        # Open Library's modern list layout varies. We check multiple high-probability 
        # selectors and return the first one that yields results.
        locators = [
            "h3.booktitle a", 
            ".list-item .title", 
            "ol-read-more a[href*='/works/']", # Targets specific work links
            ".book-item .title"
        ]
        
        all_titles = []
        for selector in locators:
            elements = self.page.locator(selector)
            count = await elements.count()
            if count > 0:
                texts = await elements.all_inner_texts()
                # Clean up whitespace and ignore empty results
                all_titles = [t.strip() for t in texts if t.strip()]
                self.logger.info(f"Successfully retrieved {len(all_titles)} titles using selector: {selector}")
                break
                
        return all_titles