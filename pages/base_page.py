from playwright.async_api import Page
from utils.performance import measure_performance

class BasePage:
    """
    Abstract Base Class for all Page Objects.
    Provides shared utilities for navigation, logging, and centralized performance monitoring.
    """
    def __init__(self, page: Page, logger):
        """
        Initializes the page object with a Playwright Page instance and a shared logger.
        Each Page Object maintains its own local performance_data buffer.
        """
        self.page = page
        self.logger = logger
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