import os
import json
import base64
from pathlib import Path
from datetime import datetime
from config import REPORTS_DIR

def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_report(results: list) -> str:
    """HTML report generate karo (HTML comparison ke liye bhi safe)"""
    Path(REPORTS_DIR).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = str(Path(REPORTS_DIR) / f"report_{timestamp}.html")

    total = len(results)
    bugs = sum(1 for r in results if r.get("ai_analysis", {}).get("is_bug", False))
    passed = total - bugs

    rows = ""
    for r in results:
        ai = r.get("ai_analysis", {})
        severity = ai.get("severity", "NONE")
        is_bug = ai.get("is_bug", False)

        severity_color = {
            "CRITICAL": "#ff4444",
            "MAJOR": "#ff8800",
            "MINOR": "#ffcc00",
            "NONE": "#00cc44"
        }.get(severity, "#888")

        status_icon = "🐛 BUG" if is_bug else "✅ OK"

        # HTML comparison ke liye baseline/current None ho sakte hain
        baseline_b64 = image_to_base64(r["baseline_path"]) if r.get("baseline_path") else ""
        current_b64 = image_to_base64(r["current_path"]) if r.get("current_path") else ""
        diff_b64 = image_to_base64(r.get("diff_path")) if r.get("diff_path") else ""

        rows += f"""
        <div class="test-card {'bug' if is_bug else 'pass'}">
            <div class="test-header">
                <h3>{r.get('test_name', 'Unknown')}</h3>
                <span class="status">{status_icon}</span>
                <span class="severity" style="background:{severity_color}">{severity}</span>
            </div>
            <div class="images">
                {f'<div class="img-box"><p>📸 Baseline</p><img src="data:image/png;base64,{baseline_b64}" /></div>' if baseline_b64 else ''}
                {f'<div class="img-box"><p>🔍 Current</p><img src="data:image/png;base64,{current_b64}" /></div>' if current_b64 else ''}
                {f'<div class="img-box"><p>🔴 Diff</p><img src="data:image/png;base64,{diff_b64}" /></div>' if diff_b64 else ''}
            </div>
            <div class="ai-analysis">
                <h4>🤖 AI Analysis</h4>
                <p><strong>Summary:</strong> {ai.get('summary', '')}</p>
                <p><strong>Details:</strong> {ai.get('details', '')}</p>
                <p><strong>Changed Elements:</strong> {', '.join(ai.get('changed_elements', []))}</p>
                <p><strong>Recommendation:</strong> {ai.get('recommendation', '')}</p>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Visual AI Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0f0f0f; color: #eee; margin: 0; padding: 20px; }}
        h1 {{ color: #00d4ff; text-align: center; }}
        .summary {{ display: flex; gap: 20px; justify-content: center; margin: 20px 0; }}
        .summary-box {{ padding: 20px 40px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }}
        .total {{ background: #1a1a2e; }}
        .passed {{ background: #0a3d0a; color: #00cc44; }}
        .failed {{ background: #3d0a0a; color: #ff4444; }}
        .test-card {{ background: #1a1a1a; border-radius: 10px; padding: 20px; margin: 20px 0; }}
        .test-card.bug {{ border-left: 5px solid #ff4444; }}
        .test-card.pass {{ border-left: 5px solid #00cc44; }}
        .test-header {{ display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }}
        .test-header h3 {{ margin: 0; color: #00d4ff; }}
        .severity {{ padding: 4px 12px; border-radius: 20px; color: #000; font-weight: bold; font-size: 12px; }}
        .images {{ display: flex; gap: 15px; margin: 15px 0; }}
        .img-box {{ flex: 1; text-align: center; }}
        .img-box img {{ width: 100%; border-radius: 8px; border: 1px solid #333; }}
        .ai-analysis {{ background: #111; padding: 15px; border-radius: 8px; margin-top: 15px; }}
        .ai-analysis h4 {{ color: #00d4ff; margin-top: 0; }}
        .ai-analysis p {{ margin: 8px 0; line-height: 1.5; }}
    </style>
</head>
<body>
    <h1>🔍 Visual AI Test Report</h1>
    <div class="summary">
        <div class="summary-box total">📊 Total: {total}</div>
        <div class="summary-box passed">✅ Passed: {passed}</div>
        <div class="summary-box failed">🐛 Bugs: {bugs}</div>
    </div>
    {rows}
    <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    return report_path
