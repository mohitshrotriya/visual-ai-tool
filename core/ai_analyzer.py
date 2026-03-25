from google import genai
import os
import json
import re
import base64

def analyze_diff(baseline_path: str, current_path: str, diff_percentage: float, api_key: str = '') -> dict:
    key = api_key or os.getenv('GEMINI_API_KEY', '')
    client = genai.Client(api_key=key)

    with open(baseline_path, "rb") as f:
        baseline_data = base64.b64encode(f.read()).decode("utf-8")
    with open(current_path, "rb") as f:
        current_data = base64.b64encode(f.read()).decode("utf-8")

    prompt = f"""
    You are a visual testing expert. Compare these two screenshots:
    - Image 1: BASELINE (expected/original)
    - Image 2: CURRENT (latest test run)
    - Pixel difference detected: {diff_percentage}%

    Respond in EXACT JSON format only:
    {{
        "is_bug": true or false,
        "severity": "CRITICAL" or "MAJOR" or "MINOR" or "NONE",
        "summary": "One line summary of what changed",
        "details": "Detailed explanation of the changes",
        "changed_elements": ["list", "of", "changed", "UI", "elements"],
        "recommendation": "What developer should do"
    }}
    Only respond with JSON, no extra text.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[
            prompt,
            {"inline_data": {"mime_type": "image/png", "data": baseline_data}},
            {"inline_data": {"mime_type": "image/png", "data": current_data}},
        ]
    )

    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        return {
            "is_bug": True,
            "severity": "MAJOR",
            "summary": "Analysis failed - manual review needed",
            "details": text,
            "changed_elements": [],
            "recommendation": "Please review manually"
        }
