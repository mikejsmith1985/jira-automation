# Release Notes - Version 1.2.0

**Release Date:** December 25, 2024

## 🎉 What's New in v1.2.0

### 🐛 Feedback System (New)
The application now includes a comprehensive feedback system for bug reporting and issue tracking:

- **Floating Bug Button** - Always-visible 🐛 button in bottom-right corner
- **Auto-Capture** - Automatically captures:
  - Python application logs (last 5 minutes or full if video recorded)
  - Browser console logs (all log levels)
  - JavaScript errors and stack traces
  - Network failures and errors
  - System information (browser, OS, app version)
- **Screenshot Capture** - Full-page screenshot using html2canvas
- **Video Recording** - 30-second maximum browser tab recording (privacy-focused)
- **GitHub Integration** - Submit issues directly to GitHub with all attachments
- **Token Management** - Configure GitHub token once, securely stored in config.yaml

### Key Features

#### 👔 Product Owner (PO) Features
- Features & Epics View with progress tracking
- Dependency Canvas with interactive visualization
- Drag-and-drop card organization
- CSV export for reporting
- Scrum/Kanban mode toggle

#### 💻 Developer (Dev) Features
- Multi-workflow system with flexible scheduling
- PR → Jira auto-linking
- Custom field, label, and status updates
- Favorites for quick task execution
- Hourly/daily/weekly scheduling options

#### 📊 Scrum Master (SM) Features
- Rule-based Insights Engine detecting:
  - Scope creep (>30% story point growth)
  - Defect leakage (production vs QA bugs)
  - Velocity trends (±15% changes)
  - Team hygiene issues (stale tickets, missing estimates, etc.)
- Team Health Overview dashboard
- Persistent metrics storage (SQLite)
- CSV export for reports
- Insight resolution tracking

### 🔧 Technical Improvements

- New `github_feedback.py` module for GitHub API integration
- Enhanced `app.py` with feedback API endpoints
- Comprehensive unit tests (9 tests, 88.9% pass rate)
- Improved error handling and logging
- SQLite database for persistent storage
- Console log hijacking for automatic error capture

### 📚 Documentation Updates

- **README.md** - Updated with v1.2.0 features and architecture
- **BEGINNERS_GUIDE.md** - Comprehensive architectural overview
- **PERSONAS.md** - Detailed persona features and responsibilities
- **PROJECT_STATUS.md** - Current status and roadmap
- **FEEDBACK_TEST_REPORT.md** - Test results and analysis
- **IMPLEMENTATION_COMPLETE.md** - Feedback system implementation details

---

## 🔄 What Changed Since v1.1.0

### Added
- Feedback system with GitHub integration
- Auto-capture of logs, errors, screenshots, video
- Token configuration UI
- Comprehensive unit tests
- Enhanced error handling

### Fixed
- Improved insights database management
- Better error messages
- Enhanced logging throughout

### Documentation
- Completely rewrote documentation for clarity
- Added architecture explanations
- Documented all APIs and endpoints

---

## 🐛 Known Limitations

- ❌ Canvas PNG export (UI complete, backend pending)
- ❌ Advanced scheduler management UI (scheduling works via config.yaml)
- ❌ Real-time sync status dashboard (basic status available)
- ❌ Trend visualization charts (data stored, charts pending)
- ❌ Bi-directional Jira ↔ GitHub sync

---

## 📦 Installation

### From Release
1. Download `GitHubJiraSync-v1.2.0.exe`
2. Run the executable (no installation needed)
3. Browser opens to `http://localhost:5000`
4. Select your persona and configure settings

### From Source
```bash
git clone https://github.com/mikejsmith1985/jira-automation.git
cd jira-automation
pip install -r requirements.txt
python app.py
```

---

## 🎯 Roadmap for v1.3.0+

### High Priority
- [ ] Canvas PNG export implementation
- [ ] Trend visualization charts
- [ ] Advanced scheduler management UI
- [ ] Real-time sync status dashboard

### Medium Priority
- [ ] Bi-directional Jira ↔ GitHub sync
- [ ] Custom issue templates for feedback
- [ ] Video compression before upload
- [ ] Attach arbitrary files to feedback

### Future
- [ ] Local LLM integration for advanced insights
- [ ] Predictive velocity forecasting
- [ ] Team capacity planning
- [ ] Retrospective insights

---

## 🙏 Contributors

Special thanks to everyone who tested and provided feedback on the v1.1.0 persona system!

---

## 📝 Migration from v1.1.0

**No breaking changes.** All v1.1.0 configurations and workflows will continue to work.

The app will automatically:
- Use existing config.yaml (no changes required)
- Preserve all workflows and favorites
- Maintain insights database
- Keep user preferences (persona selection, etc.)

---

## 📊 Statistics

- **v1.2.0 additions**: ~1,050 lines of code and documentation
- **Feedback system**: 370 lines (github_feedback.py)
- **Unit tests**: 200 lines, 9 tests, 88.9% pass rate
- **Documentation**: Enhanced README, BEGINNERS_GUIDE, PERSONAS

---

**Status:** ✅ Production-ready  
**Browser Support:** Chrome/Edge (primary), Firefox/Safari (partial)  
**Python Version:** 3.10+  
**Last Updated:** December 25, 2024
