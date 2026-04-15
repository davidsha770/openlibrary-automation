import os
import random
import re
from .base_page import BasePage

class BookPage(BasePage):
    """
    Handles book-specific interactions. 
    Implements advanced JavaScript injection to navigate and interact with 
    complex Shadow DOM elements within the Open Library UI.
    """

    async def add_to_list_specific(self, status: str) -> str:
        """
        Adds the current book to a specific reading list (e.g., 'Want to Read').
        Utilizes a recursive JavaScript search to traverse Shadow Roots that 
        standard CSS selectors cannot reach.
        """
        # We inject a script because Playwright's default selectors can sometimes struggle 
        # with nested Shadow DOMs found in Web Components like 'reading-log-button'.
        js_script = f"""
        () => {{
            function findElementRecursive(root, text) {{
                // Search for buttons within the current root (Document or ShadowRoot)
                const buttons = Array.from(root.querySelectorAll('button, .btngrp-btn'));
                let found = buttons.find(b => b.innerText.includes(text));
                if (found) return found;
                
                // Recursively dive into all Shadow Roots present in the current level
                const allElements = root.querySelectorAll('*');
                for (const el of allElements) {{
                    if (el.shadowRoot) {{
                        const result = findElementRecursive(el.shadowRoot, text);
                        if (result) return result;
                    }}
                }}
                return null;
            }}

            // Logic for 'Already Read': This status is hidden inside a dropdown menu.
            if ("{status}" === "Already Read") {{
                const host = document.querySelector('reading-log-button');
                if (host && host.shadowRoot) {{
                    // Trigger the dropdown toggle inside the Web Component
                    const arrow = host.shadowRoot.querySelector('.dropdown-toggle, .last');
                    if (arrow) {{
                        arrow.click();
                        // Allow time for the menu animation/render before selecting the option
                        return new Promise(resolve => {{
                            setTimeout(() => {{
                                const opt = findElementRecursive(document, "Already Read");
                                if (opt) {{ opt.click(); resolve(true); }}
                                else resolve(false);
                            }}, 500);
                        }});
                    }}
                }}
            }}

            // Standard execution for primary buttons (e.g., 'Want to Read')
            const btn = findElementRecursive(document, "{status}");
            if (btn) {{ btn.click(); return true; }}
            return false;
        }}
        """
        try:
            # Execute the script in the browser context
            success = await self.page.evaluate(js_script)
            return status if success else "Failed"
        except Exception as e:
            self.logger.error(f"JavaScript execution failure in add_to_list_specific: {e}")
            return "Failed"
        
    async def capture_book_addition(self, book_title: str):
        """
        Captures a visual confirmation screenshot.
        Sanitizes the book title to ensure a safe and valid filesystem filename.
        """
        screenshot_dir = os.path.join("outputs", "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Sanitize filename: replace non-alphanumeric characters with underscores
        safe_name = "".join([c if c.isalnum() else "_" for c in book_title])[:50]
        screenshot_path = os.path.join(screenshot_dir, f"{safe_name}.png")
        
        await self.page.screenshot(path=screenshot_path)
        self.logger.info(f"Visual evidence captured for '{book_title}' at {screenshot_path}")