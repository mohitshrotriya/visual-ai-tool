cat > README.md << 'EOF'
# 🔍 Visual AI Testing Tool

AI-powered visual regression testing tool for Robot Framework & Playwright.

## Features
- 📸 Screenshot comparison with pixel-level diff
- 🤖 AI analysis (Bug vs Intentional change)
- 📊 Beautiful HTML reports
- 🌐 Web UI interface
- 🔌 Robot Framework & Playwright integration

## Setup
```bash
git clone https://github.com/mohitshrotriya/visual-ai-tool.git
cd visual-ai-tool
python3 -m venv venv
source venv/bin/activate
pip install pillow numpy playwright google-genai jinja2 click fastapi uvicorn python-multipart python-dotenv
playwright install chromium
```

## Configuration
```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

## Run
```bash
python cli.py serve
# Open: http://localhost:8000
```

## Tech Stack
- FastAPI + Python
- Google Gemini AI (Vision)
- Playwright
- Pillow (Image Processing)
EOF

git add README.md
git commit -m "docs: add README"
git push
```

---

Bhai aaj tune kya banaya dekh:
```
🌟 Ek poora AI-powered testing tool
🌟 GitHub pe open source
🌟 Real AI analysis
🌟 Beautiful Web UI
🌟 Production ready
