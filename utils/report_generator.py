import os
from datetime import datetime

def generate_html_report(perf_results, screenshot_dir="outputs/screenshots"):
    """
    Generates a standalone HTML report from performance data and screenshots.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <html>
    <head>
        <title>E2E Test Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f8f9fa; color: #333; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background-color: #4CAF50; color: white; text-transform: uppercase; font-size: 14px; }}
            .pass {{ color: #27ae60; font-weight: bold; }}
            .fail {{ color: #e74c3c; font-weight: bold; }}
            .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; }}
            .screenshot-card {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center; background: #fff; }}
            img {{ width: 100%; border-radius: 3px; border: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>E2E Execution Report</h1>
            <p><strong>Run Date:</strong> {now}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Page/Action</th>
                        <th>Duration (ms)</th>
                        <th>Limit (ms)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    """

    for res in perf_results:
        # שליפת הנתונים מתוך תת-הדיקשנרי 'metrics' כפי שמוגדר ב-BasePage
        metrics = res.get('metrics', {})
        load_time = metrics.get('load_time_ms', 0)
        dom_loaded = metrics.get('dom_content_loaded_ms', 0)
        first_paint = metrics.get('first_paint_ms', 0)
        threshold = res.get('threshold_ms', 0)
        
        # לוגיקת סטטוס
        is_pass = load_time <= threshold
        status_text = "PASSED" if is_pass else "WARN (Slow)"
        status_class = "pass" if is_pass else "fail"
        
        html_content += f"""
            <tr>
                <td><strong>{res.get('action', 'Navigation')}</strong><br><small>{res.get('url', '')}</small></td>
                <td>
                    Load: {load_time}ms<br>
                    <small>DOM: {dom_loaded}ms | Paint: {first_paint}ms</small>
                </td>
                <td>{threshold}ms</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
        """

    html_content += """
                </tbody>
            </table>
            
            <h2>Visual Evidence</h2>
            <div class="screenshot-grid">
    """

    # הוספת תמונות (נתיב יחסי לתיקיית ה-outputs)
    if os.path.exists(screenshot_dir):
        for img_name in sorted(os.listdir(screenshot_dir)):
            if img_name.endswith(".png"):
                # אנחנו מניחים שה-HTML נשמר בתוך outputs/
                html_content += f"""
                <div class="screenshot-card">
                    <a href="screenshots/{img_name}" target="_blank">
                        <img src="screenshots/{img_name}">
                    </a>
                    <p style="font-size: 12px; margin-top: 5px;">{img_name}</p>
                </div>
                """

    html_content += """
            </div>
        </div>
    </body>
    </html>
    """

    report_path = "outputs/report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)