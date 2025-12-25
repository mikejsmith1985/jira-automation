# GitHub Copilot Instructions for Jira Automation Project

## Project Context

This is a **GitHub-Jira Sync Tool** that operates WITHOUT Jira REST API access. All Jira interactions use Selenium WebDriver with browser automation.

## Technical Constraints

### ❌ No Jira REST API Access
- **Do NOT** suggest or implement Jira REST API calls
- **Do NOT** use `/rest/api/` endpoints
- **Do NOT** require API tokens or OAuth for Jira
- All Jira data must be scraped from the web UI using Selenium

### ✅ Current Architecture
- **Selenium WebDriver** for Jira web scraping (manual login, session-based)
- **GitHub API** for pull request data (this is available)
- **Self-contained desktop app** with embedded web UI
- **Data structures** provided via JSON/YAML for visualization

## Persona-Based Design

The application has three distinct user personas, each with different needs:

### 1. **PO (Product Owner) Persona** 👔
**Focus**: Feature tracking and visualization
- View features/epics with child issues
- Track feature completeness and progress
- Visualize dependencies between issues
- Export data for reporting
- **Primary action**: Consuming/viewing data for decision-making
- **Data source**: Manual data structures (user provides URL or uploads data)

### 2. **Dev (Developer) Persona** 💻
**Focus**: Automation to reduce administrative burden
- Sync GitHub PR status → Jira tickets
- Auto-update tickets based on PR events (merged, closed, etc.)
- Link PRs to Jira issues automatically
- Reduce manual ticket updates
- **Primary action**: Writing data to Jira from GitHub
- **Data source**: GitHub API (automated)

### 3. **SM (Scrum Master) Persona** 📊
**Focus**: Metrics, reporting, and team hygiene
- Sprint/Kanban metrics (velocity, cycle time, throughput)
- Identify bad hygiene (stale tickets, missing info, etc.)
- Generate reports and insights
- Track team health indicators
- **Primary action**: Analytics and reporting
- **Data source**: Jira web scraping + historical data

## Key Design Patterns

### Data Input Pattern
When users need to provide Jira data for visualization:
```
1. Show clear instructions: "Create a data structure and provide the URL/file"
2. Provide JSON/YAML schema/example
3. Allow file upload or URL input
4. Parse and visualize
```

### Scrum vs Kanban Support
- Always offer toggle between Scrum and Kanban modes
- Scrum: Sprint-based metrics (velocity, burndown, sprint progress)
- Kanban: Flow-based metrics (WIP, cycle time, throughput)

### Web Scraping Approach
When scraping Jira:
```python
# Use existing driver from sync_engine
driver.get(jira_url)
# Navigate and scrape specific elements
# Parse HTML for data extraction
# Handle authentication via existing session
```

## Code Style Preferences
- Minimal comments (code should be self-explanatory)
- Small, surgical changes
- Embedded HTML/CSS/JS in single-file app where possible
- Use existing patterns from app.py

## Common Requests

### "Add a feature to the PO view"
→ Focus on visualization and export, assume data is provided

### "Add GitHub sync feature"
→ Use GitHub API, write to Jira via Selenium scraping

### "Add metrics"
→ Consider both Scrum and Kanban modes, add to SM persona

### "How do we get data from Jira?"
→ Either scrape with Selenium or ask user to provide data structure

## Project Goals
1. **Reduce dev administrative burden** (auto-sync from GitHub)
2. **Empower POs** with visual tools and dependency tracking
3. **Give SMs insights** into team health and productivity
4. **Work without API access** (Selenium-first approach)
5. **Enable user feedback** (built-in bug reporting system)

## Feedback System

### Architecture
- **Floating bug button** - Always visible, bottom-right corner
- **GitHub integration** - Submit issues via PyGithub library
- **Auto-capture** - Logs, console errors, network failures
- **Media capture** - Screenshots (html2canvas) and video (MediaRecorder API, 30s max)
- **Privacy-focused** - Browser tab recording only

### Implementation Details
- **Backend**: `github_feedback.py` with `GitHubFeedback` and `LogCapture` classes
- **Frontend**: Modal UI with screenshot/video capture
- **Storage**: GitHub Personal Access Token in config.yaml
- **Testing**: Unit tests in `test_feedback_system.py`

### Usage
1. User clicks 🐛 button
2. If no token: shows setup modal
3. User fills title/description
4. Optionally captures screenshot or 30s video
5. Logs auto-captured (last 5 mins if no video, full capture with video)
6. Submit creates GitHub issue with all attachments

## Remember
- This is a **desktop tool**, not a web service
- Users authenticate once via browser, session persists
- Favor client-side rendering over server-side
- Keep UI embedded in single Python file for easy distribution
- **Feedback system uses GitHub API** (exception to Jira no-API rule)
