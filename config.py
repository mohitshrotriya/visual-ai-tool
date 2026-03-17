import os
from dotenv import load_dotenv

load_dotenv()

# API Config
GEMINI_API_KEY = os.getenv("AIzaSyB2HkPrBYJo6yIC64tzkNnpM_SxUa-jtyU")

# Paths
BASELINES_DIR = "baselines"
REPORTS_DIR = "reports"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

# Comparison Settings
DIFF_THRESHOLD = 5.0  # 5% se zyada diff ho toh AI ko bhejo
HIGHLIGHT_COLOR = (255, 0, 0)  # Red color diff highlight ke liye

# Server Settings
HOST = "0.0.0.0"
PORT = 8000
