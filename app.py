from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
from core.compare import compare_images
from core.ai_analyzer import analyze_diff
from core.reporter import generate_report
from core.capture import save_baseline, save_current, get_baseline_path, get_current_path, baseline_exists
from config import DIFF_THRESHOLD

app = FastAPI(title="Visual AI Testing Tool")

@app.get("/", response_class=HTMLResponse)
async def home():
    return open("templates/index.html").read()

@app.post("/set-baseline")
async def set_baseline_api(test_name: str = Form(...), image: UploadFile = File(...)):
    try:
        content = await image.read()
        save_baseline(test_name, content)
        return JSONResponse({"success": True, "message": f"Baseline saved: {test_name}"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/compare")
async def compare_api(test_name: str = Form(...), image: UploadFile = File(...)):
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
        if diff_pct >= DIFF_THRESHOLD:
            ai_result = analyze_diff(baseline_path, current_path, diff_pct)

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
            "report_url": f"/reports/{report_filename}"
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