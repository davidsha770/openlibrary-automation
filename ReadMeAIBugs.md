# 🧩 Bug Analysis Report (Static Analysis)

This document outlines three critical issues identified in the provided code snippet through static analysis, as part of the "Automation Exam 2" requirements.
1. Missing await on Asynchronous Call

    location: assert function

    The Problem: The operation reading_list.get_book_count() is called without the await keyword.

    Explanation: Since the function is defined as async def, it returns a coroutine object rather than the actual integer value.

    Impact: On next line, the comparison will fail because it attempts to compare an integer (expected_count) with a coroutine object. The test will fail even if the data itself is correct.

    Fix: ```python
    actual = await reading_list.get_book_count()
    ```

2. Brittle Year Parsing (Data Type / Parsing Error)

    location: search function

    The Problem: The code attempts to directly cast a trimmed string to an integer: int(year_text.strip()).

    Explanation: Year data on sites like Open Library often contains non-numeric text, such as "1980 (first published)" or "c2005".

    Impact: Python will raise a ValueError and the program will crash as soon as it encounters a character that is not a digit.

    Fix: ```python
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

    Fix: ```python
    import os
    Ensure the directory exists before saving the screenshot

    os.makedirs("screenshots", exist_ok=True)
    await page.screenshot(path=f"screenshots/{url}.png")
    ```