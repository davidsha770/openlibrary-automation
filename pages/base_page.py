import json
import os
from playwright.async_api import Page
from utils.performance import PerformanceMonitor

class BasePage:
    def __init__(self, page: Page, logger):
        self.page = page
        self.logger = logger
        self.performance_data = []

    async def measure_page_performance(self, url: str, threshold_ms: int, action_name: str = "Navigation") -> dict:
        """
        סעיף 4: תיקון הפרת SRP.
        עדכון: שימוש ב-Wait Strategy יציב יותר למניעת Timeouts.
        """
        try:
            if self.page.url != url:
                # שינוי מ-networkidle ל-load כדי למנוע את ה-Timeout שראינו בלוג
                await self.page.goto(url, wait_until="load", timeout=30000)
            
            # קריאה ל-Utility המודרני (סעיף 5)
            metrics = await PerformanceMonitor.capture_modern_metrics(self.page)
            
            # טיפול במקרה שהמדידה נכשלה או לא שלמה
            load_time = metrics.get('load_time_ms', 999999) # Default גבוה אם אין נתון
            
            # אם ה-Utility החזיר סטטוס Incomplete, נתעד זאת
            is_incomplete = metrics.get('status') == "Incomplete"
            
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
            # כאן נכנסים ה-Timeouts של ה-goto
            self.logger.error(f"Failed performance measurement for {url}: {e}")
            # מוסיפים רשומה של כישלון לדו"ח כדי שלא ייעלם
            self.performance_data.append({
                "action": action_name,
                "url": url,
                "status": "Error",
                "error": str(e)
            })
            return {}

    def save_performance_report(self, file_path: str = "outputs/performance_report.json"):
        # נשאר אותו דבר, רק מוודא שהנתיב קיים
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.performance_data, f, indent=4)