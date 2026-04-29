# 🧩 Bug Analysis Report (Static Analysis)

This document outlines three critical issues identified in the provided code snippet through static analysis, as part of the "Automation Exam 2" requirements.
1. Missing await on Asynchronous Call

    location: assert function

    The Problem: The operation reading_list.get_book_count() is called without the await keyword.

    Explanation: Since the function is defined as async def, it returns a coroutine object rather than the actual integer value.

    Impact: On next line, the comparison will fail because it attempts to compare an integer (expected_count) with a coroutine object. The test will fail even if the data itself is correct.

    Fix:
    ```python
    actual = await reading_list.get_book_count()
    ```

2. Brittle Year Parsing (Data Type / Parsing Error)

    location: search function

    The Problem: The code attempts to directly cast a trimmed string to an integer: int(year_text.strip()).

    Explanation: Year data on sites like Open Library often contains non-numeric text, such as "1980 (first published)" or "c2005".

    Impact: Python will raise a ValueError and the program will crash as soon as it encounters a character that is not a digit.

    Fix:
    ```python
    import re
    # Extract only the numeric digits from the string

    year_match = re.search(r'\d+', year_text)
    year = int(year_match.group()) if year_match else 0
    ```

3. Resource Management Error (File System)

    location: add book function

    The Problem: The script attempts to save a screenshot to a path that might not exist: screenshots/{url}.png.

    Explanation: If the screenshots directory was not manually created beforehand, the system will not create it automatically during runtime.

    Impact: This results in a FileNotFoundError (or a Playwright-specific directory error), causing the automation to terminate prematurely.

    Fix:
    ```python
    import os
    Ensure the directory exists before saving the screenshot

    os.makedirs("screenshots", exist_ok=True)
    await page.screenshot(path=f"screenshots/{url}.png")
    ```

4. Ambiguous Selector for Submit Action

    Location: BookSearchPage class.
    The Problem: The selector for the search button is a generic button[type='submit'].
    Explanation: OpenLibrary often has multiple submit buttons (e.g., search bar and login forms).
    Impact: Playwright may click the wrong button or throw a strict mode violation error because the selector resolves to multiple elements.
    Fix:
    ```python
    self.search_button = "form[action='/search'] button[type='submit']"
    ```

5. Stale Element / SPA Race Condition

    Location: search_books_by_title_under_year function.
    The Problem: The script clicks the next page button but immediately breaks the loop  or proceeds without waiting for new content.
    Explanation: Since the site utilizes dynamic loading, clicking "Next" requires waiting for the DOM to update.
    Impact: The script may scrape the old Page 1 results again or fail to find the new elements, leading to duplicate or missing data.
    Fix:
    ```python
    await next_btn.click()
    await page.wait_for_selector(".searchResultItem") # Wait for new results to render
    ```

6. Incorrect Result Container Identification

    Location: ReadingListPage class.
    The Problem: The locator looks for .listbook-item to count books.
    Explanation: The actual DOM for OpenLibrary reading lists typically uses different classes (e.g., .sri--w-main or specific list identifiers).
    Impact: query_selector_all will return an empty list even if books are present. The test will report 0 books, causing a false failure in the assertion.
    Fix:
    ```python
    items = await self.page.query_selector_all(".searchResultItem") # Use the verified result class
    ```

7. Logical Logic Flow (Pagination)

    Location: search_books_by_title_under_year loop.
    The Problem: The next_btn is assigned inside a conditional check, and the click() happens outside of proper page-load synchronization.
    Explanation: The current structure tries to click the next button after finding just one book under the year, rather than after checking all items on the page.
    Impact: Inefficient scraping and premature termination of the search process.
    Fix:
    ```python
    # The pagination logic should be moved outside the result-parsing 'for' loop
    # to ensure all items on the current page are processed first.
    ```