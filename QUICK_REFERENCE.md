# 🚀 Quick Reference Guide

**Waypoint** - Simplifying Jira administration and team flow

---

## 📖 Documentation Map

### For Different Audiences

**New Users** 👤
```
START HERE → README.md
THEN → PERSONAS.md (find your role)
THEN → config.yaml (configure your instance)
```

**Developers** 👨‍💻
```
START HERE → BEGINNERS_GUIDE.md (architecture)
THEN → app.py (main web server)
THEN → sync_engine.py (orchestration)
THEN → PROJECT_STATUS.md (roadmap)
```

**Product Managers** 📊
```
START HERE → PERSONAS.md (understand users)
THEN → PROJECT_STATUS.md (completion status)
THEN → RELEASE_NOTES.md (version history)
```

**QA/Testing** 🧪
```
START HERE → PERSONAS.md (all features)
THEN → FEEDBACK_TEST_REPORT.md (what was tested)
THEN → PROJECT_STATUS.md (what's ready)
```

---

## 🎯 Quick Start

### Installation
```bash
pip install -r requirements.txt
python app.py
# Browser opens to http://localhost:5000
```

### Configuration
Edit `config.yaml`:
```yaml
jira:
  base_url: "https://your-company.atlassian.net"
  
github:
  organization: "your-org"
  repositories: ["repo1", "repo2"]
```

### First Sync
1. Open web UI
2. Click "Initialize" (opens browser for Jira login)
3. Go to Dev tab
4. Click "Sync Now"

---

## 🏗️ Architecture Overview

```
Web UI (Browser)
    ↓
HTTP Server (app.py)
    ↓
Orchestrator (sync_engine.py)
    ├─→ Read GitHub (github_scraper.py + Selenium)
    ├─→ Write Jira (jira_automator.py + Selenium)
    ├─→ Detect Patterns (insights_engine.py)
    └─→ Store Data (feedback_db.py + SQLite)
```

---

## 👥 Three Personas

### 👔 Product Owner
- **Focus:** Feature tracking and dependencies
- **Tab:** PO
- **Key Tool:** Dependency Canvas
- **Config:** Manual JSON upload

### 💻 Developer
- **Focus:** GitHub → Jira automation
- **Tab:** Dev
- **Key Tool:** Workflows (config.yaml)
- **Config:** GitHub org + repos, Jira custom fields

### 📊 Scrum Master
- **Focus:** Team health and metrics
- **Tab:** SM
- **Key Tool:** Insights Engine
- **Config:** Thresholds in config.yaml

---

## 📋 File Purposes

| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | Overview & quick start | Everyone |
| `BEGINNERS_GUIDE.md` | Deep architecture | Developers |
| `PERSONAS.md` | Feature descriptions | Everyone |
| `PROJECT_STATUS.md` | What's done/next | Developers/PMs |
| `RELEASE_NOTES.md` | Version history | Users |
| `config.yaml` | Configuration | Users |
| `app.py` | Web server + UI | Developers |
| `sync_engine.py` | Orchestration | Developers |
| `github_scraper.py` | GitHub reading | Developers |
| `jira_automator.py` | Jira updating | Developers |
| `insights_engine.py` | Pattern detection | Developers |
| `feedback_db.py` | Data storage | Developers |
| `github_feedback.py` | Feedback system | Developers |

---

## 🔧 Common Tasks

### Add a New Workflow
```yaml
# In config.yaml, under workflows:
my_workflow:
  enabled: true
  schedule:
    frequency: "daily"
    time: "09:00"
  pr_opened:
    add_comment: true
    labels: ["has-pr"]
```

### Add Custom Field Mapping
```yaml
# In config.yaml, under jira.custom_fields:
my_field: "customfield_12345"
```

### Check Logs
```bash
tail -f jira-sync.log
# or
sqlite3 data/insights.db "SELECT * FROM insights;"
```

### Submit Feedback
- Click 🐛 button in app
- Takes automatic screenshot, logs, optionally video
- Submits to GitHub as issue

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.10+ from python.org |
| Import errors | `pip install -r requirements.txt` |
| Can't connect to Jira | Check base_url in config.yaml |
| PRs not syncing | Check GitHub org/repos in config.yaml |
| Insights not showing | Run hygiene check in SM tab |
| Token errors | Add GitHub token in Settings tab |

---

## 📊 Feature Status

✅ **Complete (v1.2.0)**
- Multi-persona system
- GitHub-Jira auto-sync
- Insights engine
- Feedback system
- Database persistence
- CSV exports

⏳ **Planned (v1.3.0+)**
- Canvas PNG export
- Trend charts
- Advanced scheduler UI
- Bi-directional sync
- LLM integration

---

## 🔐 Security Notes

- Uses existing Jira browser session (no credentials stored)
- GitHub token stored in config.yaml (consider encrypting)
- No cloud dependencies
- All data stays local

---

## 📞 Help & Support

**Documentation**
- README.md - Quick start
- BEGINNERS_GUIDE.md - Deep dive
- PERSONAS.md - Features by role

**Support**
- Use 🐛 feedback button in app
- Check logs: `jira-sync.log`
- Inspect database: `sqlite3 data/insights.db`

---

## 🎓 Learning Path

1. **Understand:** Read PERSONAS.md (5 min)
2. **Install:** Follow README.md (2 min)
3. **Configure:** Edit config.yaml (5 min)
4. **Explore:** Click around web UI (10 min)
5. **Use:** Try first sync from Dev tab (5 min)
6. **Customize:** Add workflow to config.yaml (10 min)
7. **Deep Dive:** Read BEGINNERS_GUIDE.md (30 min)

---

## 🚀 Version Info

**Current:** 1.2.0 (Feedback System)  
**Python:** 3.10+  
**Browser:** Chrome/Edge (primary), Firefox/Safari (partial)  
**Status:** Production-ready  

---

**Last Updated:** December 25, 2024  
**For more info:** See README.md or BEGINNERS_GUIDE.md
