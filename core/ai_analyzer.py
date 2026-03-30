from google import genai
import os
import json
import re
import base64

def analyze_diff(baseline_path: str, current_path: str, diff_percentage: float, api_key: str = '') -> dict:
    key = api_key.strip() or os.getenv('GEMINI_API_KEY', '').strip()
    
    if not key or len(key) < 30:
        return {
            "is_bug": True,
            "severity": "MAJOR",
            "summary": "Gemini API Key missing or invalid",
            "details": "Valid Gemini API key daalo.",
            "changed_elements": [],
            "recommendation": "Google AI Studio se naya API key banao"
        }

    try:
        client = genai.Client(api_key=key)

        with open(baseline_path, "rb") as f:
            baseline_data = base64.b64encode(f.read()).decode("utf-8")
        with open(current_path, "rb") as f:
            current_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = f"""You are an expert QA Automation Engineer doing visual regression testing.

Compare these two screenshots:
- Image 1: BASELINE (expected)
- Image 2: CURRENT (latest)

Pixel difference: {diff_percentage}%

Respond ONLY in exact JSON format:
{{
  "is_bug": true or false,
  "severity": "CRITICAL" or "MAJOR" or "MINOR" or "NONE",
  "summary": "One line summary",
  "details": "Detailed explanation",
  "changed_elements": ["list", "of", "changed", "elements"],
  "recommendation": "What to do next"
}}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",   # ← Yeh change kar diya
            contents=[
                prompt,
                {"inline_data": {"mime_type": "image/png", "data": baseline_data}},
                {"inline_data": {"mime_type": "image/png", "data": current_data}}
            ]
        )

        text = response.text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            result = json.loads(json_match.group())
            result.setdefault("is_bug", True)
            result.setdefault("severity", "MAJOR")
            return result

    except Exception as e:
        error_str = str(e)[:400]
        print(f"Gemini Error: {error_str}")

    return {
        "is_bug": True,
        "severity": "MAJOR",
        "summary": "AI Analysis could not complete",
        "details": f"Technical error: {error_str}",
        "changed_elements": [],
        "recommendation": "Naya API key try karo ya thodi der baad retry karo"
    }

def analyze_html_diff(html1: str, html2: str, test_name: str) -> dict:
    """Do HTML code ko compare kare aur detailed report de"""
    key = os.getenv('GEMINI_API_KEY', '')
    if not key:
        return {"is_bug": True, "severity": "MAJOR", "summary": "API Key missing", "details": "Gemini API key nahi mili", "changed_elements": [], "recommendation": "API key set karo"}

    try:
        client = genai.Client(api_key=key)

        prompt = f"""
You are an expert Frontend QA Engineer. Compare these two HTML snippets:

HTML 1 (Baseline):
{html1}

HTML 2 (Current):
{html2}

Respond ONLY in exact JSON format:
{{
  "is_bug": true or false,
  "severity": "CRITICAL" or "MAJOR" or "MINOR" or "NONE",
  "summary": "One line summary of main changes",
  "details": "Detailed explanation",
  "same_ids": ["list", "of", "same", "IDs"],
  "changed_elements": ["list of changed elements"],
  "added_elements": ["list of added elements"],
  "removed_elements": ["list of removed elements"],
  "changed_attributes": ["list of changed attributes"],
  "recommendation": "What developer should do"
}}
Only return valid JSON, no extra text.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )

        text = response.text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL | re.IGNORECASE)

        if json_match:
            result = json.loads(json_match.group())
            result.setdefault("is_bug", True)
            return result

    except Exception as e:
        print(f"HTML Analysis Error: {e}")

    return {
        "is_bug": True,
        "severity": "MAJOR",
        "summary": "HTML comparison failed",
        "details": "Technical error occurred while comparing HTML",
        "same_ids": [],
        "changed_elements": [],
        "added_elements": [],
        "removed_elements": [],
        "changed_attributes": [],
        "recommendation": "Manual review karo"
    }
    