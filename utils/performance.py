import os
import json
from playwright.async_api import Page
from urllib.parse import urljoin, urlparse

async def capture_modern_metrics(page: Page) -> dict:
    """
    Extracts high-accuracy performance metrics from the browser.
    Includes a short delay to ensure Paint events are registered by the browser.
    """
    # Allow the browser a moment to register paint events
    await page.wait_for_function(
        "() => performance.getEntriesByType('navigation')[0]?.loadEventEnd > 0",
        timeout=10000
    )
    
    metrics_js = """
    () => {
        const [nav] = performance.getEntriesByType("navigation");
        const paint = performance.getEntriesByType('paint');
        const fp = paint.find(entry => entry.name === 'first-paint');
        
        if (!nav) return {};

        const startTime = nav.startTime;
        
        return {
            "load_time_ms": Math.round(nav.loadEventEnd - startTime),
            "dom_content_loaded_ms": Math.round(nav.domContentLoadedEventEnd - startTime),
            "first_paint_ms": fp ? Math.round(fp.startTime) : 0,
            "status": nav.loadEventEnd > 0 ? "Complete" : "Incomplete"
        };
    }
    """
    return await page.evaluate(metrics_js)

async def measure_performance(page: Page, url: str, threshold: int, label: str, logger) -> dict:
    """
    REQUIRED FUNCTION: Standalone performance measurement utility.
    Complies with technical specifications and Single Responsibility Principle (SRP).
    """
    try:
        # Navigate to URL if not already present
        current_path = urlparse(page.url).path.rstrip('/')
        target_path = urlparse(url).path.rstrip('/')
        if current_path != target_path:
            await page.goto(url, wait_until="domcontentloaded")
        
        metrics = await capture_modern_metrics(page)
        load_time = metrics.get('load_time_ms', 0)
        if load_time <= 0:
            status = "Error"
            logger.error(f"PERFORMANCE ERROR: Captured invalid load time (0ms) for {label}. Check page state.")
        else:
            # Determine pass/fail status based on threshold
            status = "Pass" if load_time <= threshold else "Fail"
            if status == "Fail":
                logger.warning(f"PERFORMANCE FAIL: {label} took {load_time}ms (Threshold: {threshold}ms)")
            
        return {
            "action": label,
            "url": url,
            "metrics": metrics,
            "status": status,
            "threshold_ms": threshold
        }
    except Exception as e:
        logger.error(f"Performance measurement error: {e}")
        return {"action": label, "status": "Error", "error": str(e)}
    
def save_performance_report(performance_data: list, file_path: str = "outputs/performance_report.json"):
    """
    Exports the captured metrics list to a structured JSON file.
    Automatically creates the output directory if it does not exist.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(performance_data, f, indent=4)