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

app = FastAPI(title="Visual AI Testing Tool")

@app.get("/", response_class=HTMLResponse)
async def home():
    return open("templates/index.html").read()

def highlight_bugs(current_path: str, diff_image, test_name: str) -> str:
    """Bug wali jagah pe red rectangle draw karo"""
    import numpy as np
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

def log_to_sheets(sheet_id: str, sheet_name: str, test_name: str, ai_result: dict, diff_pct: float):
    """Bug ko Google Sheet mein log karo"""
    try:
        creds_path = "credentials.json"
        if not os.path.exists(creds_path):
            return False
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        if sheet.row_count < 1 or sheet.cell(1, 1).value != "Test Name":
            sheet.append_row(["Test Name", "Severity", "Bug Description", "Details", "Diff %", "Status", "Date"])
        sheet.append_row([
            test_name,
            ai_result.get("severity", ""),
            ai_result.get("summary", ""),
            ai_result.get("details", ""),
            f"{diff_pct}%",
            "Open",
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ])
        return True
    except Exception as e:
        print(f"Sheets error: {e}")
        return False

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
    sheet_id: str = Form(default=""),
    sheet_name: str = Form(default="Bug Reports")
):
    try:
        if not baseline_exists(test_name):
            return JSONResponse({"success": False, "error": f"Baseline nahi mili: {test_name}"})

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
        sheet_logged = False

        if diff_pct >= DIFF_THRESHOLD:
            # Use user's API key if provided
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key

            ai_result = analyze_diff(baseline_path, current_path, diff_pct)

            # Bug Highlighting
            if ai_result.get("is_bug"):
                highlighted_path = highlight_bugs(current_path, result["diff_image"], test_name)
                highlighted_url = f"/images/{test_name}/highlighted.png"

                # Google Sheets logging
                if sheet_id:
                    sheet_logged = log_to_sheets(sheet_id, sheet_name, test_name, ai_result, diff_pct)

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
            "sheet_logged": sheet_logged
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
