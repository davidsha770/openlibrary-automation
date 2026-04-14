import json
import os
from playwright.async_api import Page
from utils.performance import PerformanceMonitor

class BasePage:
    """
    Base class for all page objects. 
    Provides shared utilities for performance monitoring and navigation.
    """
    def __init__(self, page: Page, logger):
        self.page = page
        self.logger = logger
        self.performance_data = []

    async def measure_page_performance(self, url: str, threshold_ms: int, action_name: str = "Navigation") -> dict:
        """
        Measures page load performance using modern web metrics.
        Uses a stable wait strategy (load instead of networkidle) to prevent flaky timeouts.
        """
        try:
            # Navigate only if not already on the target URL
            if self.page.url != url:
                # Changed from 'networkidle' to 'load' to avoid 30s timeouts 
                # caused by persistent background analytics/scripts.
                await self.page.goto(url, wait_until="load", timeout=30000)
            
            # Capture performance metrics using the PerformanceMonitor utility
            metrics = await PerformanceMonitor.capture_modern_metrics(self.page)
            
            # Fallback for missing or incomplete metrics
            load_time = metrics.get('load_time_ms', 999999) 
            is_incomplete = metrics.get('status') == "Incomplete"
            
            # Determine success status based on threshold and completeness
            status = "Pass" if (load_time <= threshold_ms and not is_incomplete) else "Fail"
            
            report_entry = {
                "action": action_name,
                "url": url,
                "metrics": metrics,
                "threshold_ms": threshold_ms,
                "status": status
            }

            self.performance_data.append(report_entry)
            
            if status == "Fail":
                reason = "Threshold exceeded" if load_time > threshold_ms else "Incomplete load"
                self.logger.warning(f"PERFORMANCE FAIL: {action_name} ({reason}). Took {load_time}ms")
            
            return metrics

        except Exception as e:
            # Handle navigation or measurement timeouts
            self.logger.error(f"Failed performance measurement for {url}: {e}")
            
            # Log the error in the report so it is not omitted from final results
            self.performance_data.append({
                "action": action_name,
                "url": url,
                "status": "Error",
                "error": str(e)
            })
            return {}

    def save_performance_report(self, file_path: str = "outputs/performance_report.json"):
        """
        Exports all captured performance data to a JSON file.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.performance_data, f, indent=4)