# Jira Hygiene Assistant - Python Edition

A self-contained desktop application for automated Jira ticket hygiene checks using browser automation.

## ✨ Features

- 🔍 **Find stale tickets** - Tickets with no updates in 7+ days
- 📝 **Find missing descriptions** - Tickets without descriptions
- 📅 **Find missing due dates** - Tickets lacking due dates
- 🔧 **Custom JQL queries** - Run any Jira Query Language search
- 💬 **Bulk actions** - Add comments to multiple tickets at once
- 🌐 **Browser automation** - Works through Jira web UI (no API needed)
- 📦 **Self-contained** - Single .exe file, no installation required

## 🚀 Quick Start

### Running the Packaged Application:

1. Download `JiraHygieneAssistant.exe`
2. Double-click to run
3. Browser will open automatically to http://localhost:5000
4. Enter your Jira URL and click "Connect to Jira"
5. Log in to Jira in the browser window that opens
6. Use the app to run queries and perform bulk actions

## 🛠️ Development Setup

### Prerequisites:

- Python 3.10+ ([Download](https://www.python.org/downloads/))
- pip (comes with Python)

### Installation:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Run the app
python app.py
```

The app will start and open http://localhost:5000 in your browser.

## 📦 Building the Executable

Create a build script to package as standalone .exe:

```powershell
# See build.ps1 for automated build process
.\build.ps1
```

Output: `dist\JiraHygieneAssistant.exe`

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Web UI (Embedded HTML/JS)              │
│  - Configuration form                   │
│  - Query buttons                        │
│  - Results display                      │
│  - Bulk action controls                 │
└────────────────┬────────────────────────┘
                 │ HTTP (localhost:5000)
                 ↓
┌─────────────────────────────────────────┐
│  Flask Backend (Python)                 │
│  - REST API endpoints                   │
│  - Session management                   │
│  - Query orchestration                  │
└────────────────┬────────────────────────┘
                 │ Playwright API
                 ↓
┌─────────────────────────────────────────┐
│  Browser Automation (Playwright)        │
│  - Chromium browser control             │
│  - Navigate Jira web UI                 │
│  - Extract ticket data                  │
│  - Add comments via UI                  │
└─────────────────────────────────────────┘
```

## 📂 Project Structure

```
jira-automation/
├── app.py                  # Main Flask application with embedded UI
├── requirements.txt        # Python dependencies
├── build.ps1              # Build script (creates .exe)
└── README.md              # This file
```

## 🚨 Troubleshooting

### App won't start:

**Problem:** "Python not found" or module errors
```bash
# Solution: Ensure Python 3.10+ is installed
python --version

# Reinstall dependencies
pip install -r requirements.txt
playwright install chromium
```

### Browser automation fails:

**Problem:** Can't find Jira elements
- **Cause:** Jira's HTML structure varies by version
- **Solution:** Update selectors in `app.py`

**Problem:** Session expired
- **Cause:** Not logged into Jira
- **Solution:** Log in manually when browser window opens

## 🔐 Security

- ✅ **No credential storage** - Uses your browser session
- ✅ **Local only** - Runs on localhost
- ✅ **Transparent** - Watch browser automation in real-time
- ✅ **Open source** - All code is reviewable

## 📝 Changelog

### Version 1.0.0 (Current)

- ✅ Flask web server with embedded UI
- ✅ Playwright browser automation
- ✅ Pre-built hygiene queries
- ✅ Custom JQL support
- ✅ Bulk comment functionality

### Planned Features:

- [ ] More bulk actions (assign, transition)
- [ ] Export results to CSV
- [ ] Scheduled automation
- [ ] Query templates

## 📄 License

MIT License

---

**Built with ❤️ for teams who need Jira automation without API access**
