import os
import random
import re
from .base_page import BasePage

class BookPage(BasePage):
    """
    Handles book-specific actions, utilizing direct JavaScript injection 
    to interact with complex Shadow DOM elements in the Open Library UI.
    """

    async def add_to_list_specific(self, status: str) -> str:
        """
        Adds a book to a specific status (e.g., 'Want to Read' or 'Already Read').
        Uses recursive Shadow DOM searching to locate buttons.
        """
        js_script = f"""
        () => {{
            function findElementRecursive(root, text) {{
                const buttons = Array.from(root.querySelectorAll('button, .btngrp-btn'));
                let found = buttons.find(b => b.innerText.includes(text));
                if (found) return found;
                
                const allElements = root.querySelectorAll('*');
                for (const el of allElements) {{
                    if (el.shadowRoot) {{
                        const result = findElementRecursive(el.shadowRoot, text);
                        if (result) return result;
                    }}
                }}
                return null;
            }}

            // If target is 'Already Read', the dropdown menu must be opened first
            if ("{status}" === "Already Read") {{
                const host = document.querySelector('reading-log-button');
                if (host && host.shadowRoot) {{
                    const arrow = host.shadowRoot.querySelector('.dropdown-toggle, .last');
                    if (arrow) {{
                        arrow.click();
                        // Wait briefly for the menu animation to complete before clicking the option
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

            // Standard click for primary buttons or as a fallback
            const btn = findElementRecursive(document, "{status}");
            if (btn) {{ btn.click(); return true; }}
            return false;
        }}
        """
        try:
            success = await self.page.evaluate(js_script)
            return status if success else "Failed"
        except Exception as e:
            self.logger.error(f"JavaScript execution error in add_to_list_specific: {e}")
            return "Failed"
        
    async def capture_book_addition(self, book_title: str):
        """
        Captures a screenshot after adding a book. 
        Sanitizes the book title for a safe filename.
        """
        screenshot_dir = os.path.join("outputs", "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Create a filesystem-friendly name from the book title
        safe_name = "".join([c if c.isalnum() else "_" for c in book_title])[:50]
        screenshot_path = os.path.join(screenshot_dir, f"{safe_name}.png")
        
        await self.page.screenshot(path=screenshot_path)
        self.logger.info(f"Screenshot saved for '{book_title}' at {screenshot_path}")