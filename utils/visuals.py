import os

async def capture_book_addition(book_title: str, page, logger):
    """
    Captures a visual confirmation screenshot.
    Sanitizes the book title to create a valid filesystem filename.
    """
    screenshot_dir = os.path.join("outputs", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
        
    # Replace non-alphanumeric characters with underscores for safe filenames
    safe_name = "".join([c if c.isalnum() else "_" for c in book_title])[:50]
    screenshot_path = os.path.join(screenshot_dir, f"{safe_name}.png")
    
    await page.screenshot(path=screenshot_path)
    logger.info(f"Visual evidence captured for '{book_title}' at {screenshot_path}")
    return screenshot_path