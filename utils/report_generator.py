import os
from datetime import datetime

def generate_html_report(perf_results, screenshot_dir="outputs/screenshots"):
    """
    Generates a lightweight, standalone HTML report.
    Integrates performance Web Vitals (FCP, DOM Load) and visual evidence (screenshots)
    into a single, portable file for quick stakeholder review.
    """
    # Timestamp for the test execution run
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Styled HTML template using a modern, clean CSS design
    html_content = f"""
    <html>
    <head>
        <title>E2E Execution Report</title>
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
            .screenshot-card {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            img {{ width: 100%; border-radius: 3px; border: 1px solid #eee; transition: transform 0.2s; }}
            img:hover {{ transform: scale(1.05); }} /* Subtle hover effect for better UX */
        </style>
    </head>
    <body>
        <div class="container">
            <h1>E2E Test Execution Summary</h1>
            <p><strong>Run Date:</strong> {now}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Page/Action Scope</th>
                        <th>Performance Metrics</th>
                        <th>Threshold</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    """

    for res in perf_results:
        # Extract technical metrics captured via the Browser Performance API
        metrics = res.get('metrics', {})
        load_time = metrics.get('load_time_ms', 0)
        dom_loaded = metrics.get('dom_content_loaded_ms', 0)
        first_paint = metrics.get('first_paint_ms', 0)
        threshold = res.get('threshold_ms', 0)
        
        # Validation Logic: Determine if the page load meets the defined SLA (Threshold)
        is_pass = load_time <= threshold
        status_text = "PASSED" if is_pass else "FAIL (SLA Breach)"
        status_class = "pass" if is_pass else "fail"
        
        html_content += f"""
            <tr>
                <td><strong>{res.get('action', 'Navigation')}</strong><br><small>{res.get('url', '')}</small></td>
                <td>
                    <strong>Load: {load_time}ms</strong><br>
                    <small>DOM: {dom_loaded}ms | First Paint: {first_paint}ms</small>
                </td>
                <td>{threshold}ms</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
        """

    html_content += """
                </tbody>
            </table>
            
            <h2>Visual Evidence (Screenshots)</h2>
            <div class="screenshot-grid">
    """

    # Dynamically inject captured screenshots into the grid
    if os.path.exists(screenshot_dir):
        for img_name in sorted(os.listdir(screenshot_dir)):
            if img_name.endswith(".png"):
                # Path logic assumes the HTML file is stored in the 'outputs' directory
                html_content += f"""
                <div class="screenshot-card">
                    <a href="screenshots/{img_name}" target="_blank">
                        <img src="screenshots/{img_name}" alt="{img_name}">
                    </a>
                    <p style="font-size: 11px; margin-top: 8px; color: #666;">{img_name}</p>
                </div>
                """

    html_content += """
            </div>
        </div>
    </body>
    </html>
    """

    # Write the final buffer to a static HTML file
    report_path = "outputs/report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)