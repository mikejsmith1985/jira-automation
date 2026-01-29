# Waypoint: GitHub-Jira Sync Tool
**Simplifying Jira administration and team flow.**

A self-contained desktop application that syncs GitHub PRs with Jira tickets and provides team insights, all using browser automation (no API access required).

## ✨ Core Features

### 👔 Product Owner (PO) Persona
- **Features & Epics View** - Track feature completeness with visual progress bars
- **Dependency Canvas** - Interactive visualization of issue dependencies with drag-and-drop
- **Team Mode Toggle** - Switch between Scrum (velocity) and Kanban (WIP, cycle time) metrics
- **Export Reports** - Download feature tracking and dependency data as CSV

### 💻 Developer (Dev) Persona
- **GitHub → Jira Auto-Sync** - Link PRs to Jira tickets via commit messages and branch names
- **Multi-Workflow System** - Define custom workflows for different scenarios (hourly, daily, weekly)
- **Flexible Updates** - Update multiple fields, labels, and statuses per ticket
- **Favorites** - Save common tasks for one-click execution
- **Batch fixVersion Creator** - Create multiple release versions from date lists with custom formatting

### 📊 Scrum Master (SM) Persona
- **Team Health Insights** - Rule-based detection of scope creep, defect leakage, stale tickets
- **Hygiene Reports** - Identify missing estimates, long-running stories, blocked items
- **Trend Analysis** - Track velocity, cycle time, and throughput over time
- **Batch fixVersion Creator** - Create multiple release versions from date lists with custom formatting
- **SQLite Persistence** - Store insights and metrics history locally

### 🐛 Feedback System
- **Floating Bug Button** - Always-visible feedback modal in app corner
- **Auto-Capture** - Logs, console errors, screenshots, and 30-second video recordings
- **GitHub Integration** - Submit issues directly from the app with all attachments
- **Privacy-Focused** - Browser tab recording only, no full-screen capture

## 🚀 Quick Start

### Running from Source (Development):

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py
```

The app starts automatically and opens http://localhost:5000 in your browser.

### Key Features Quick Access:

**Create fixVersions (SM Persona)**:
1. Open Waypoint app (http://localhost:5000)
2. Click **SM** tab in sidebar
3. Scroll to "Create fixVersions" card
4. Enter project key and dates
5. Click "Create Versions"

See **[FIXVERSION_WAYPOINT_INTEGRATION.md](FIXVERSION_WAYPOINT_INTEGRATION.md)** for detailed instructions.

### Running the Packaged Application:

1. Download `GitHubJiraSync.exe` from releases
2. Double-click to run
3. Browser opens to http://localhost:5000
4. Select your persona (PO, Dev, or SM)
5. Configure your Jira URL and GitHub organization in Settings

## 🛠️ Development Setup

### Prerequisites:

- Python 3.10+ ([Download](https://www.python.org/downloads/))
- pip (comes with Python)

### Installation:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 📦 Building the Executable

```powershell
# Build standalone .exe with PyInstaller
.\build.ps1
```

Output: `dist\GitHubJiraSync.exe` (~50MB self-contained executable)

## 🏗️ Architecture

The application uses a **Selenium-based browser automation** approach with a Python HTTP server and embedded web UI:

```
┌─────────────────────────────────────────────┐
│  Web UI (Embedded HTML/JS/CSS)              │
│  - Persona selection (PO/Dev/SM)            │
│  - Dashboard, Workflows, Insights, Settings │
│  - Dependency Canvas visualization          │
│  - Feedback modal with attachments          │
└────────────────┬────────────────────────────┘
                 │ HTTP (localhost:5000)
                 ↓
┌─────────────────────────────────────────────┐
│  Python HTTP Server (app.py)                │
│  - REST API endpoints                       │
│  - Workflow orchestration                   │
│  - Insights engine processing               │
│  - Feedback system handling                 │
│  - SQLite database management               │
└────────────────┬────────────────────────────┘
                 │ Selenium API
                 ↓
┌─────────────────────────────────────────────┐
│  Browser Automation (Selenium WebDriver)    │
│  - Chrome/Chromium browser control          │
│  - Navigate Jira web UI                     │
│  - Extract ticket data (scraping)           │
│  - Update tickets (field, label, status)    │
│  - Add comments to issues                   │
└─────────────────────────────────────────────┘
```

### Key Components

- **app.py** - HTTP server, web UI, API endpoints, workflow orchestration
- **sync_engine.py** - Coordinates GitHub scraping with Jira automation
- **github_scraper.py** - Extracts PR information from GitHub web UI
- **jira_automator.py** - Updates Jira tickets via browser automation
- **jira_version_creator.py** - Batch creates fixVersions from date lists
- **insights_engine.py** - Rule-based pattern detection (scope creep, defects, hygiene)
- **feedback_db.py** - SQLite storage for insights, metrics, and logs
- **github_feedback.py** - GitHub API integration for issue submission
- **config.yaml** - Workflow definitions, field mappings, scheduling rules

## 🚨 Troubleshooting

### App won't start:

**Problem:** "Python not found" or module errors
```bash
# Ensure Python 3.10+ is installed
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### Browser automation fails:

**Problem:** Can't find Jira elements or page won't load
- **Cause:** Jira HTML structure may vary by version or instance
- **Solution:** Update CSS selectors in `jira_automator.py`

**Problem:** Session expired or login loops
- **Cause:** Browser not logged into Jira
- **Solution:** Browser window will appear on first run - log in manually

**Problem:** PRs not syncing from GitHub
- **Cause:** GitHub scraping depends on GitHub's HTML structure
- **Solution:** Check GitHub hasn't changed their PR page layout; update selectors in `github_scraper.py`

### fixVersion Creator issues:

**Problem:** "Could not find Create Version button"
- **Cause:** Need admin/project lead permissions in Jira
- **Solution:** Ask your Jira admin for project permissions

**Problem:** Versions not showing up
- **Solution:** Refresh Jira versions page, or check they didn't already exist
- **See:** `FIXVERSION_QUICKSTART.md` for full troubleshooting

### Database issues:

**Problem:** Insights not appearing or persisting
- **Solution:** Delete `data/insights.db` and restart the app to rebuild

### Feedback system not working:

**Problem:** "No token configured" message
- **Solution:** Go to Settings, add your GitHub Personal Access Token (create at https://github.com/settings/tokens)
- **Required scopes:** `repo` (full control of private repositories)

## 🔐 Security & Privacy

- ✅ **Browser Session Based** - Uses existing Jira login, no credentials stored
- ✅ **No Cloud Dependencies** - All data stays local by default
- ✅ **Transparent** - Watch browser automation in real-time
- ✅ **Privacy-First Video** - Records browser tab only, not full screen
- ✅ **Open Source** - All code is reviewable on GitHub
- ⚠️ **Note:** GitHub token stored in `config.yaml`. For production, consider encrypting sensitive config values.

## 📝 Changelog

### Version 1.2.0 (Current - Feedback System)
- ✅ Floating bug button feedback modal
- ✅ Auto-capture console logs, errors, screenshots, and 30s video
- ✅ GitHub issue submission with attachments
- ✅ Privacy-focused (browser tab recording only)
- ✅ Comprehensive unit tests (9 tests, 88.9% pass rate)

### Version 1.1.0
- ✅ Persona-based interface (PO/Dev/SM)
- ✅ Dependency Canvas with drag-and-drop
- ✅ Rule-based Insights Engine
- ✅ Team hygiene detection
- ✅ SQLite persistence for metrics
- ✅ Scrum/Kanban mode toggle
- ✅ Export features and reports to CSV

### Version 1.0.0
- ✅ GitHub-Jira sync via browser automation
- ✅ Multi-workflow system with scheduling
- ✅ Favorites system for quick tasks
- ✅ Custom JQL query support
- ✅ Multiple field updates per ticket
- ✅ Comprehensive logging

## 🎯 Planned Features (v1.3.0+)

- [ ] Canvas PNG export
- [ ] Real-time sync status dashboard
- [ ] Advanced scheduler management (start/stop/pause)
- [ ] Trend visualization charts
- [ ] PDF/PowerPoint report exports
- [ ] Integration with local LLM for advanced insights
- [ ] Bi-directional Jira ↔ GitHub sync

## 📄 License

MIT License

---

**Built with ❤️ for teams who need Jira automation without API access**
