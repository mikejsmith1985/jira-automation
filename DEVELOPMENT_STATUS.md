# Jira Hygiene Assistant v1.0.0

🎉 **Python-based self-contained desktop application for automated Jira hygiene checks**

## ✅ What Works

✔️ Python app with embedded web UI  
✔️ Playwright browser automation (interacts with Jira web UI, no API needed)  
✔️ Find stale tickets, missing descriptions, missing due dates  
✔️ Custom JQL queries  
✔️ Bulk comment functionality  
✔️ Can be packaged to single .exe with PyInstaller  

## 🚀 Quick Start (Development)

1. Install dependencies:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

2. Run the app:
```bash
python app.py
```

3. Browser opens automatically to http://localhost:5000
4. Enter your Jira URL and start automating!

## 📦 Building Standalone EXE

Run the build script:
```powershell
.\build.ps1
```

This creates `dist\JiraHygieneAssistant.exe` - a self-contained executable.

## 🏗️ Architecture

- **Python HTTP Server** - Built-in http.server (no Flask/C++ dependencies)
- **Playwright** - Browser automation for Jira web UI interaction
- **Embedded HTML/JS** - Single-file web interface
- **PyInstaller** - Packages everything into one .exe

Based on the proven architecture of forge-terminal (works in locked-down environments).

## 📝 Next Steps

- [ ] Test with real Jira instance
- [ ] Refine element selectors for different Jira versions
- [ ] Add more bulk actions (assign, transition, update fields)
- [ ] Package and test the .exe
- [ ] Create GitHub release with binary

## 🔧 Troubleshooting

- **Selectors not working?** Update `page.query_selector_all()` calls in app.py for your Jira version
- **Browser won't launch?** Run `python -m playwright install chromium`
- **Build fails?** Ensure PyInstaller is installed: `pip install pyinstaller`

---

**Status**: Ready for testing! 🎯
