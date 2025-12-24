# Release Notes - Version 1.1.0

**Release Date:** December 24, 2024

## 🎉 Major Features

### Persona-Based Interface
The application now supports three distinct user personas, each with tailored features:

- **👔 Product Owner (PO)**: Feature tracking, dependency visualization, progress monitoring
- **💻 Developer (Dev)**: GitHub automation, reduced admin work, PR-to-ticket sync
- **📈 Scrum Master (SM)**: Team health insights, hygiene reports, metrics tracking

Users can select their persona on the dashboard to see relevant quick actions while maintaining access to all features.

### Interactive Dependency Canvas
- Visual representation of issue dependencies with drag-and-drop cards
- Three link types: Blocks (red dashed), Depends On (green numbered), Related (blue)
- Support for uploading dependency data via JSON file or URL
- Export canvas to PNG (UI ready)

### Rule-Based Insights Engine
Automated pattern detection without AI/LLM:

- **Scope Creep**: Detects stories with >30% point growth after sprint start
- **Defect Leakage**: Tracks production bugs and escape rate (>20% alert)
- **Velocity Trends**: Identifies significant changes (±15%)
- **Team Hygiene**: 
  - Stale tickets (14+ days no update)
  - Missing story point estimates
  - Long-running stories (>10 days in progress)
  - Blocked items with duration tracking

### Persistent Insights Storage
- SQLite database for storing insights and metrics history
- Historical trend tracking for velocity, WIP, cycle time
- Insight resolution system (mark as resolved)
- Time-series data for long-term analysis

### Export Features
- Export features to CSV with progress and status
- Export hygiene reports to CSV
- Export dependency canvas to PNG (coming soon)

### Scrum/Kanban Support
Toggle between team methodologies:
- **Scrum**: Sprint metrics, velocity, sprint progress
- **Kanban**: WIP count, cycle time, throughput

## 🔧 Technical Improvements

- New `insights_engine.py` module with comprehensive rule-based analysis
- SQLite backend with indexed queries for performance
- API endpoints for insights retrieval, resolution, and trend data
- Enhanced UI with persona-specific tabs and actions
- Configurable thresholds in `config.yaml`

## 📚 Documentation Updates

- **New**: `.github/copilot-instructions.md` - Development guidelines
- **New**: `PERSONAS.md` - Detailed persona design document
- **New**: `LOCAL_LLM_PLAN.md` - Future AI integration roadmap
- **Updated**: `README.md` - Comprehensive feature documentation
- **Updated**: `DEVELOPMENT_STATUS.md` - Current status and roadmap
- **Updated**: `PROJECT_STATUS.md` - Version 1.1.0 status

## 🐛 Bug Fixes

- Fixed localStorage persona persistence
- Improved error handling in insights API endpoints
- Enhanced database connection management

## ⚠️ Known Limitations

- Canvas PNG export UI ready but implementation pending
- Insights based on sample data until Jira scraper integration complete
- Scheduler stop functionality not yet implemented
- GitHub automation rules UI complete but backend integration pending

## 🔄 Migration Notes

No breaking changes from v1.0.0. The application will automatically:
- Create `data/insights.db` on first run
- Migrate existing config.yaml (no changes required)
- Preserve all existing workflows and favorites

## 📦 Installation

### From Release
1. Download `GitHubJiraSync-v1.1.0.exe` (Windows)
2. Run the executable
3. Browser opens to `http://localhost:5000`
4. Select your persona and start using the tool

### From Source
```bash
git clone https://github.com/yourusername/jira-automation.git
cd jira-automation
git checkout v1.1.0
pip install -r requirements.txt
python app.py
```

## 🎯 Next Steps (v1.2.0 Roadmap)

- Integrate insights engine with real Jira scraper
- Complete GitHub automation rule execution
- Implement canvas PNG export
- Add scheduler management (start/stop/configure)
- Trend visualization charts
- PDF/PowerPoint report exports

## 🙏 Contributors

Special thanks to all contributors who helped shape the persona design and insights system!

---

**Full Changelog**: https://github.com/yourusername/jira-automation/compare/v1.0.0...v1.1.0
