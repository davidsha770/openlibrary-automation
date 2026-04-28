from playwright.async_api import Page
import os
from utils.performance import measure_performance

class BasePage:
    """
    Abstract Base Class for all Page Objects.
    Provides shared utilities for navigation, logging, and centralized performance monitoring.
    """
    def __init__(self, page: Page, logger, config: dict):
        """
        Initializes the page object with a Playwright Page instance and a shared logger.
        Each Page Object maintains its own local performance_data buffer.
        """
        self.page = page
        self.logger = logger
        self.config = config
        self.performance_data = []

    async def measure_page_performance(self, url: str, threshold: int, action_name: str):
        """
        Orchestrates page-level performance measurement by delegating to the 
        standalone performance utility (following Single Responsibility Principle).
        
        Appends the resulting metrics to the local performance buffer for reporting.
        """
        # Call the standalone measurement utility - Ensures clean SRP compliance
        result = await measure_performance(self.page, url, threshold, action_name, self.logger)
        self.performance_data.append(result)
        return result
    
    async def report_error(self, e: Exception, message: str, screenshot_name: str = None, level: str = "error"):
        """
        Centralized error reporting mechanism.
        Handles logging and visual evidence without duplicating code in every page object.
        """
        # Dynamically call the appropriate logger level (info, warning, error, debug)
        log_func = getattr(self.logger, level)
        log_func(f"{message}: {e}")
        
        if screenshot_name:
            # Ensure the output directory exists
            os.makedirs("outputs", exist_ok=True)
            path = f"outputs/{screenshot_name}.png"
            await self.page.screenshot(path=path)
            self.logger.info(f"Visual evidence captured: {path}")