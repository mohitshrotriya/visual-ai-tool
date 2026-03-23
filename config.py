import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
BASELINES_DIR = "baselines"
REPORTS_DIR = "reports"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"
DIFF_THRESHOLD = 5.0
HIGHLIGHT_COLOR = (255, 0, 0)
HOST = "0.0.0.0"
PORT = 8000
