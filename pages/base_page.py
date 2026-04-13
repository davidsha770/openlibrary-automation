import time
import json
import os
from playwright.async_api import Page

class BasePage:
    def __init__(self, page: Page, logger):
        """
        Initializes the base page with Playwright page object and a logger.
        """
        self.page = page
        self.logger = logger
        # Accumulates all performance metrics captured during the session
        self.performance_data = []

    async def measure_page_performance(self, url: str, threshold_ms: int, action_name: str = "Navigation") -> dict:
        """
        Navigates to a URL (if not already there) and captures performance metrics.
        Metrics include First Paint, DOM Content Loaded, and Total Load Time.
        Results are appended to the cumulative performance report.
        """
        start_time = time.perf_counter()
        
        try:
            # Navigate only if the current URL is different from the target
            if self.page.url != url:
                await self.page.goto(url, wait_until="networkidle")
            
            # Execute JS in browser context to retrieve Navigation Timing API data
            metrics = await self.page.evaluate("""() => {
                const timing = window.performance.timing;
                const paint = performance.getEntriesByType('paint');
                const firstPaint = paint.find(entry => entry.name === 'first-paint');
                
                return {
                    load_time_ms: Math.round(timing.loadEventEnd - timing.navigationStart),
                    dom_content_loaded_ms: Math.round(timing.domContentLoadedEventEnd - timing.navigationStart),
                    first_paint_ms: firstPaint ? Math.round(firstPaint.startTime) : 0
                };
            }""")
            
            # Fallback calculation if the browser API returns incomplete data
            if metrics['load_time_ms'] <= 0:
                metrics['load_time_ms'] = round((time.perf_counter() - start_time) * 1000)

            # Validate metrics against the provided threshold
            status = "Pass" if metrics['load_time_ms'] <= threshold_ms else "Fail"
            
            report_entry = {
                "action": action_name,
                "url": url,
                "metrics": metrics,
                "threshold_ms": threshold_ms,
                "status": status
            }

            self.performance_data.append(report_entry)
            
            if status == "Fail":
                self.logger.warning(
                    f"PERFORMANCE WARNING: {action_name} at {url} took {metrics['load_time_ms']}ms (Threshold: {threshold_ms}ms)"
                )
            
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to measure performance for {url}: {e}")
            return {}

    def save_performance_report(self, file_path: str = "outputs/performance_report.json"):
        """
        Exports the cumulative performance data to a JSON file.
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.performance_data, f, indent=4)
            self.logger.info(f"Performance report saved to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save performance report: {e}")