# 👥 User Personas - Feature & Responsibility Map

This application is designed around three distinct user personas, each with specific goals and workflows. All personas can access the entire app, but each tab highlights features most relevant to their role.

---

## 👔 PO (Product Owner) Persona

**Primary Goal**: Visualize and track feature/epic completeness and dependencies for strategic decision-making

### Current Features ✅

#### Features & Epics View
- **Progress Tracking** - See all features with child issues and completion percentage
- **Status Visibility** - Expandable cards showing all child issues and their statuses
- **Status Filters** - Filter by In Progress, Completed, Blocked, etc.
- **Export to CSV** - Download feature tracking data for reports and presentations

**Data Source**: Manual data upload (user provides JSON/YAML structure)

#### Dependency Canvas
- **Interactive Visualization** - See how issues block each other
- **Three Link Types**:
  - 🔴 Blocks/Blocked (red dashed lines)
  - 🟢 Depends On (green numbered lines for sequence)
  - 🔵 Related (blue lines)
- **Drag-and-Drop Cards** - Organize the view to your needs
- **Import from JSON/URL** - Load dependency data from file or web URL
- **Issue Details** - Click cards to see detailed information

**Data Source**: Manual JSON upload (user creates dependency structure)

#### Team Mode Support
- **🏃 Scrum Mode**
  - Sprint progress percentage
  - Velocity metrics
  - Sprint burn-down information
- **🌊 Kanban Mode**
  - WIP (Work in Progress) count
  - Cycle time metrics
  - Throughput indicators

### Primary Actions
✅ **Consume/View** data for decision-making  
✅ **Export** reports for stakeholders  
✅ **Track** feature completeness  
✅ **Identify** blocked or at-risk work  
✅ **Plan** releases based on dependencies  

### Key Questions This Persona Answers
- "What's the status of our Q1 roadmap?"
- "Which features are blocked?"
- "Can we ship this release?"
- "What dependencies need to be resolved?"
- "What's the completion percentage for each epic?"

---

## 💻 Dev (Developer) Persona

**Primary Goal**: Reduce administrative burden by automating Jira updates from GitHub activities

### Current Features ✅

#### Multi-Workflow System
- **Flexible Scheduling**
  - Hourly (during business hours or always)
  - Daily (at specific time)
  - Weekly (specific day and time)
  - Per-workflow configuration
- **Custom Rules** - Define what happens for each PR event
- **Multiple Workflows** - Run different rules for different scenarios

#### Automation Rules

**When PR is Opened**
```
- Add comment with PR link
- Add label (e.g., "has-pr")
- Update PR Link custom field
- Optionally change status
```

**When PR is Updated**
```
- Add comment with update notification
- Update metadata
```

**When PR is Merged**
```
- Add comment notification
- Add "merged" label
- Move ticket to "Done" status
```

**When PR is Closed (not merged)**
```
- Add comment explaining closure
- Add "pr-closed" label
```

#### Favorites System
- **Save Common Tasks** - Create named favorites for frequently used workflows
- **One-Click Execution** - Run complex updates with single click
- **Template Support** - Reuse configurations with minor tweaks

#### Custom Workflows (via config.yaml)
- **JQL-Based Workflows** - Run custom Jira queries instead of PR-based
- **Field Mapping** - Map custom fields by their IDs
- **Comment Templates** - Use variables like {pr_url}, {author}, {branch_name}
- **Label Management** - Add multiple labels per update
- **Status Transitions** - Move tickets between statuses

### Supported Variables in Templates
```
{pr_url}           - Full URL to the PR
{branch_name}      - Git branch name
{author}           - PR author username
{commit_message}   - Latest commit message
{merger}           - Person who merged the PR
{pr_number}        - PR number (without repo)
{repo}             - Repository name
{org}              - Organization name
```

### Primary Actions
✅ **Automate** Jira updates from GitHub  
✅ **Link** PRs to tickets automatically  
✅ **Reduce** manual ticket maintenance  
✅ **Execute** bulk updates via favorites  
✅ **Schedule** recurring sync tasks  

### Key Questions This Persona Answers
- "Can we automatically update tickets when PRs are opened?"
- "Can we mark tickets done when PR is merged?"
- "How do we ensure all PRs are linked to Jira?"
- "Can we run syncs on a schedule?"
- "How do we reduce time spent updating tickets manually?"

### Data Sources
- **GitHub** - Pull requests, commits, branch names, authors (via Selenium scraping)
- **Jira** - Tickets for updates (via browser automation)
- Fully automated, no manual data entry required

---

## 📊 SM (Scrum Master) Persona

**Primary Goal**: Identify team issues, track team health metrics, and drive process improvements

### Current Features ✅

#### Team Health Overview
- **Key Metrics Dashboard**
  - Current sprint/iteration health
  - Team velocity
  - Cycle time
  - WIP (Work in Progress)
  - Throughput

#### Insights Engine (Rule-Based Pattern Detection)

**Scope Creep Detection**
- Monitors story point changes after sprint start
- Alerts when stories grow by >30%
- Shows which stories changed and by how much
- Helps prevent mid-sprint scope explosion

**Defect Leakage Detection**
- Tracks bugs linked to "Done" stories
- Calculates production vs QA bug ratio
- Alerts when escape rate exceeds 20%
- Helps improve quality processes

**Velocity Trends**
- Tracks velocity sprint-to-sprint
- Identifies significant changes (±15%)
- Shows trend direction
- Helps with capacity planning and forecasting

**Team Hygiene Checks**
- **Stale Tickets** - No updates in 14+ days (zombie work)
- **Missing Story Points** - Stories without estimates
- **Long Runners** - Stories in progress >10 days (stuck work)
- **Blocked Items** - Stories blocked for extended periods
- **Missing Assignees** - Unassigned work items
- **Missing Acceptance Criteria** - Stories without definition

#### Hygiene Report Export
- Export all hygiene issues to CSV
- Include severity levels
- Include descriptions and recommendations
- Use for team discussions and retrospectives

#### Persistent Metrics Storage
- **SQLite Database** - Historical data stored locally
- **Trend Analysis** - See changes over weeks/months
- **Data Retention** - Keep full history for analysis
- **Query Support** - Run custom queries on database

#### Insight Resolution System
- **Mark as Resolved** - Track which insights you've addressed
- **Auto-Filter** - Resolved insights hidden from default view
- **Timestamp Tracking** - See when insights were generated and resolved
- **Audit Trail** - Full history of insight lifecycle

### Primary Actions
✅ **Analyze** team performance and trends  
✅ **Identify** process bottlenecks  
✅ **Generate** reports for stakeholders  
✅ **Coach** team on process improvements  
✅ **Track** quality metrics over time  

### Key Questions This Persona Answers
- "How is our velocity trending?"
- "Are we stalling on any work?"
- "Do we have scope creep in our current sprint?"
- "What's our defect escape rate?"
- "Which tickets need attention?"
- "Is our team capacity increasing or decreasing?"
- "Where are the bottlenecks in our process?"

### Data Sources
- **Jira** - Story points, status changes, dates (via Selenium scraping)
- **GitHub** - Bug tracking and PR metrics (via scraping)
- Historical data automatically accumulated in SQLite
- Can import custom data structures for analysis

---

## 🔄 Cross-Persona Features

### Feedback System (All Personas)
- **🐛 Floating Bug Button** - Report issues from anywhere in the app
- **Auto-Capture** - Logs, console errors, screenshots, video
- **GitHub Integration** - Issues submitted directly to GitHub
- **Rich Diagnostics** - Help developers debug faster
- **Privacy-Focused** - Browser tab recording only

### Settings (All Personas)
- Configure Jira URL and authentication
- Set GitHub organization and repositories
- Manage custom field mappings
- Toggle feedback system settings
- View configuration status

### Logs Tab (All Personas)
- View detailed sync operation logs
- See what workflows ran and when
- Check for errors and warnings
- Export logs for debugging

---

## 🎯 Design Principles

### Data Access Patterns
1. **PO Persona**: Manual data input (user creates and provides structures)
2. **Dev Persona**: Automated GitHub monitoring + Jira updates
3. **SM Persona**: Jira scraping + metric aggregation + pattern detection

### Why No Jira API?
- Team has no Jira API access available
- Selenium WebDriver works around this limitation
- Uses existing browser authentication, no tokens needed
- Equally effective for our use cases

### Scrum vs Kanban Support
All personas can toggle between methodologies:
- **Scrum**: Sprint-based metrics, velocity, sprint goals
- **Kanban**: Flow-based metrics, WIP limits, cycle time
- Users match their team's workflow

### Extensibility Design
- **Workflow configuration in YAML** - No code changes needed
- **Custom field mapping** - Works with any Jira configuration
- **Rule-based insights** - Easy to add new detection rules
- **Modular architecture** - Each component can be extended independently

---

## 📋 Feature Completeness

| Feature | Status | Persona |
|---------|--------|---------|
| Feature tracking view | ✅ Complete | PO |
| Dependency canvas | ✅ Complete | PO |
| CSV export | ✅ Complete | PO/SM |
| Scrum/Kanban toggle | ✅ Complete | All |
| Workflow system | ✅ Complete | Dev |
| PR auto-linking | ✅ Complete | Dev |
| Favorites | ✅ Complete | Dev |
| Scheduling | ✅ Complete | Dev |
| Insights engine | ✅ Complete | SM |
| Hygiene checks | ✅ Complete | SM |
| Database persistence | ✅ Complete | SM |
| Feedback system | ✅ Complete | All |
| Settings | ✅ Complete | All |

---

## 🔮 Future Enhancements (Not Yet Implemented)

### PO Enhancements
- [ ] Roadmap timeline view (Gantt charts)
- [ ] Release planning tools
- [ ] Risk/dependency heatmaps
- [ ] Export to PowerPoint/PDF

### Dev Enhancements
- [ ] Bi-directional sync (Jira → GitHub branches)
- [ ] Auto-create branches from tickets
- [ ] PR template integration
- [ ] Code review reminders

### SM Enhancements
- [ ] Predictive analytics (velocity forecasting)
- [ ] Team capacity planning
- [ ] Retrospective insights
- [ ] Custom report builder
- [ ] Advanced scheduler UI

---

## 🎓 How to Use This Document

- **If you're a PO:** Skim to "PO Persona" section - that's your primary tool
- **If you're a Dev:** Focus on "Dev Persona" - setup your workflows in config.yaml
- **If you're an SM:** Check "SM Persona" - run insights to find team issues
- **If you're customizing:** Read "Design Principles" for architecture decisions

---

**Built with the belief that different users have different needs, and good software meets users where they are.**
