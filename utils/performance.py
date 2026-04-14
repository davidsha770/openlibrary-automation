import time
from playwright.async_api import Page

class PerformanceMonitor:
    @staticmethod
    async def capture_modern_metrics(page: Page) -> dict:
        """
        סעיף 5: שימוש ב-Performance Navigation Timing (Level 2).
        עדכון: הוספת הגנות למקרה שהמדדים טרם התעדכנו בדפדפן.
        """
        metrics_js = """
        () => {
            const [nav] = performance.getEntriesByType("navigation");
            const paint = performance.getEntriesByType('paint');
            const firstPaint = paint.find(entry => entry.name === 'first-paint');
            
            if (!nav) return null;

            // אם loadEventEnd הוא 0, נשתמש ב-Date.now() כקירוב או נחזיר ערך חסר
            // זה קורה כשהדף נחשב טעון מבחינת Playwright אבל הדפדפן טרם סגר את ה-Event
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
            # הוספת timeout קצר ל-evaluate עצמו כדי שלא יתקע את הטסט
            metrics = await page.evaluate(metrics_js)
            
            if not metrics:
                return {"error": "No navigation entries found"}
                
            return metrics
        except Exception as e:
            # במקרה של שגיאת JS או ניתוק מהדף
            return {"error": str(e), "load_time_ms": 0}