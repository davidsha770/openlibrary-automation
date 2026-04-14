import time
from playwright.async_api import Page

class PerformanceMonitor:
    """
    Utility class for capturing detailed web performance metrics using 
    Performance Navigation Timing (Level 2).
    """
    @staticmethod
    async def capture_modern_metrics(page: Page) -> dict:
        """
        Executes JavaScript in the browser context to capture precise timing metrics.
        Includes protections for cases where metrics are not yet fully updated by the browser.
        """
        metrics_js = """
        () => {
            const [nav] = performance.getEntriesByType("navigation");
            const paint = performance.getEntriesByType('paint');
            const firstPaint = paint.find(entry => entry.name === 'first-paint');
            
            if (!nav) return null;

            // If loadEventEnd is 0, the browser hasn't officially closed the event.
            // We use performance.now() as a fallback approximation to avoid reporting 0ms.
            const loadTime = nav.loadEventEnd > 0 
                ? nav.loadEventEnd - nav.startTime 
                : performance.now() - nav.startTime;

            return {
                "load_time_ms": Math.round(loadTime),
                "dom_content_loaded_ms": Math.round(nav.domContentLoadedEventEnd - nav.startTime),
                "first_paint_ms": firstPaint ? Math.round(firstPaint.startTime) : 0,
                "response_time_ms": Math.round(nav.responseEnd - nav.responseStart),
                "status": nav.loadEventEnd > 0 ? "Complete" : "Incomplete"
            };
        }
        """
        try:
            # Execute the JS snippet with a short timeout to prevent blocking the test
            metrics = await page.evaluate(metrics_js)
            
            if not metrics:
                return {"error": "No navigation entries found"}
                
            return metrics
        except Exception as e:
            # Handle potential JS errors or page disconnections
            return {"error": str(e), "load_time_ms": 0}