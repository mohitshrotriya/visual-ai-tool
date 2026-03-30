from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
from core.compare import compare_images
from core.ai_analyzer import analyze_diff
from core.reporter import generate_report
from core.capture import save_baseline, save_current, get_baseline_path, get_current_path, baseline_exists
from config import DIFF_THRESHOLD
from PIL import Image, ImageDraw
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import numpy as np

app = FastAPI(title="Visual AI Testing Tool")


@app.get("/", response_class=HTMLResponse)
async def home():
    return open("templates/index.html").read()


def highlight_bugs(current_path: str, diff_image, test_name: str) -> str:
    current = Image.open(current_path).convert("RGB")
    diff_array = np.array(diff_image)
    draw = ImageDraw.Draw(current)
    diff_mask = diff_array[:, :, 0] > 100
    rows = np.any(diff_mask, axis=1)
    cols = np.any(diff_mask, axis=0)
    if rows.any() and cols.any():
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        padding = 10
        draw.rectangle(
            [max(0, cmin-padding), max(0, rmin-padding),
             min(current.width, cmax+padding), min(current.height, rmax+padding)],
            outline=(255, 0, 0), width=4
        )
    highlighted_path = str(Path("baselines") / test_name / "highlighted.png")
    current.save(highlighted_path)
    return highlighted_path


def log_to_sheets(test_name: str, ai_result: dict, diff_pct: float) -> str:
    """Har bug ke liye AUTOMATICALLY naya Google Sheet banaye aur URL return kare"""
    try:
        creds_path = "credentials.json"
        if not os.path.exists(creds_path):
            print("❌ credentials.json nahi mila")
            return ""

        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)

        # Naya sheet ka naam with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet_title = f"QAMS Bug Report - {test_name} - {timestamp}"

        # Naya spreadsheet create karo
        new_sheet = client.create(title=sheet_title)

        # Header aur data daalo
        worksheet = new_sheet.sheet1
        worksheet.update('A1', [
            ["Test Name", "Severity", "Summary", "Details", "Changed Elements", "Diff %", "Date"]
        ])

        row = [
            test_name,
            ai_result.get("severity", "MAJOR"),
            ai_result.get("summary", ""),
            ai_result.get("details", ""),
            ", ".join(ai_result.get("changed_elements", [])),
            f"{diff_pct}%",
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ]
        worksheet.append_row(row)

        # Publicly viewable bana do
        new_sheet.share(None, perm_type='anyone', role='reader')

        sheet_url = new_sheet.url
        print(f"✅ Naya Google Sheet bana: {sheet_url}")
        return sheet_url

    except Exception as e:
        print(f"Sheets creation error: {e}")
        return ""


@app.post("/set-baseline")
async def set_baseline_api(test_name: str = Form(...), image: UploadFile = File(...)):
    try:
        content = await image.read()
        save_baseline(test_name, content)
        return JSONResponse({"success": True, "message": f"Baseline saved: {test_name}"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@app.post("/compare")
async def compare_api(
    test_name: str = Form(...),
    image: UploadFile = File(...),
    api_key: str = Form(default=""),
):
    try:
        if not baseline_exists(test_name):
            return JSONResponse({"success": False, "error": f"Baseline nahi mili: {test_name}"})

        if not api_key or len(api_key) < 20:
            return JSONResponse({"success": False, "error": "Valid API key provide karo — Change Key button dabao"})

        content = await image.read()
        save_current(test_name, content)

        baseline_path = get_baseline_path(test_name)
        current_path = get_current_path(test_name)

        result = compare_images(baseline_path, current_path)
        diff_pct = result["diff_percentage"]

        diff_path = str(Path("baselines") / test_name / "diff.png")
        result["diff_image"].save(diff_path)

        ai_result = {}
        highlighted_url = None
        sheet_url = ""                     # ← Naya variable

        if diff_pct >= DIFF_THRESHOLD:
            ai_result = analyze_diff(baseline_path, current_path, diff_pct, api_key)

            if ai_result.get("is_bug"):
                highlighted_path = highlight_bugs(current_path, result["diff_image"], test_name)
                highlighted_url = f"/images/{test_name}/highlighted.png"

                # ← Naya sheet create karo
                sheet_url = log_to_sheets(test_name, ai_result, diff_pct)

        report_path = generate_report([{
            "test_name": test_name,
            "baseline_path": baseline_path,
            "current_path": current_path,
            "diff_path": diff_path,
            "diff_percentage": diff_pct,
            "ai_analysis": ai_result
        }])

        report_filename = Path(report_path).name

        return JSONResponse({
            "success": True,
            "diff_percentage": diff_pct,
            "ai_analysis": ai_result,
            "baseline_url": f"/images/{test_name}/baseline.png",
            "current_url": f"/images/{test_name}/current.png",
            "diff_url": f"/images/{test_name}/diff.png",
            "highlighted_url": highlighted_url,
            "report_url": f"/reports/{report_filename}",
            "sheet_url": sheet_url,           # ← Naya URL return ho raha hai
            "sheet_logged": bool(sheet_url)
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@app.get("/images/{test_name}/{filename}")
async def get_image(test_name: str, filename: str):
    path = Path("baselines") / test_name / filename
    if path.exists():
        return FileResponse(str(path))
    return JSONResponse({"error": "Image nahi mili"}, status_code=404)


@app.get("/reports/{filename}")
async def get_report(filename: str):
    path = Path("reports") / filename
    if path.exists():
        return FileResponse(str(path))
    return JSONResponse({"error": "Report nahi mili"}, status_code=404)


@app.post("/compare-html")
async def compare_html_api(
    test_name: str = Form(...),
    html1: str = Form(...),
    html2: str = Form(...),
    api_key: str = Form(default="")
):
    try:
        if not api_key or len(api_key) < 20:
            return JSONResponse({"success": False, "error": "Valid Gemini API key provide karo"})

        from core.ai_analyzer import analyze_html_diff
        ai_result = analyze_html_diff(html1, html2, test_name)

        # Simple HTML report generate (basic)
        report_path = generate_report([{
            "test_name": test_name,
            "baseline_path": None,
            "current_path": None,
            "diff_path": None,
            "diff_percentage": 0,
            "ai_analysis": ai_result
        }])

        report_filename = Path(report_path).name

        return JSONResponse({
            "success": True,
            "ai_analysis": ai_result,
            "report_url": f"/reports/{report_filename}"
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})