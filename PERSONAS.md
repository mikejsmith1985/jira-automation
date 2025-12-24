# Persona-Based Design

This application is designed around three distinct user personas, each with specific needs and workflows.

## 👔 PO (Product Owner) Persona

**Primary Goal**: Visualize and track feature/epic completeness for decision-making

### Key Features
- **Features & Epics View**
  - See all features with child issues
  - Visual progress bars showing completion percentage
  - Expandable cards to see all child issues and their statuses
  - Filter by status (In Progress, Completed, Blocked)

- **Dependency Canvas**
  - Interactive visualization of issue dependencies
  - Drag-and-drop cards to organize view
  - Three link types:
    - 🔴 Blocks/Blocked (red dashed lines)
    - 🟢 Depends On (green numbered lines for sequence)
    - 🔵 Related (blue lines)
  - Import dependency data via JSON file or URL

- **Team Mode Support**
  - Toggle between Scrum and Kanban
  - Scrum: Sprint progress, velocity
  - Kanban: WIP, cycle time, throughput

### Primary Actions
- **Consume/View** data for decision-making
- **Export** reports and visualizations
- **Track** feature completeness
- **Identify** blocked or at-risk work

### Data Sources
- Manual data structures (JSON/YAML)
- User-provided URLs or file uploads
- Exported reports from other tools

---

## 💻 Dev (Developer) Persona

**Primary Goal**: Reduce administrative burden by automating Jira updates from GitHub

### Key Features
- **GitHub → Jira Sync**
  - Auto-link PRs to Jira issues (via commit messages, branch names)
  - Auto-update Jira ticket status when PR is merged
  - Update ticket comments with PR links
  - Sync PR review status to Jira

- **Automated Workflows**
  - PR merged → Move ticket to "Done"
  - PR opened → Add comment with link
  - PR closed → Update ticket status
  - Schedule regular syncs

### Primary Actions
- **Write** data to Jira (via Selenium scraping)
- **Automate** status updates
- **Link** PRs to tickets
- **Reduce** manual ticket maintenance

### Data Sources
- **GitHub API** (pull requests, commits, reviews)
- Automated, no manual data entry required

---

## 📊 SM (Scrum Master) Persona

**Primary Goal**: Metrics, reporting, and identifying team health issues

### Key Features
- **Sprint/Kanban Metrics**
  - Velocity tracking (Scrum)
  - Cycle time and throughput (Kanban)
  - Burndown/burnup charts
  - Cumulative flow diagrams

- **Team Hygiene Reports**
  - Stale tickets (no updates in X days)
  - Missing story points/estimates
  - Tickets without assignees
  - Blockers not addressed
  - Missing acceptance criteria
  - Tickets in wrong status

- **Trend Analysis**
  - Velocity trends over sprints
  - Average cycle time trends
  - Blocker frequency
  - Work distribution across team

### Primary Actions
- **Analyze** team performance
- **Identify** process issues
- **Generate** reports for stakeholders
- **Coach** team on improvements

### Data Sources
- Jira web scraping (via Selenium)
- Historical data exports
- GitHub data (for PR metrics)

---

## Design Philosophy

### Data Access Pattern
1. **PO Persona**: Manual data input (user creates and provides structure)
2. **Dev Persona**: Automated GitHub API pulls + Selenium writes to Jira
3. **SM Persona**: Selenium web scraping + data aggregation

### Why No Jira API?
- **Constraint**: No Jira REST API access available
- **Solution**: Use Selenium WebDriver to scrape Jira web UI
- **Benefit**: Works with existing browser authentication, no API tokens needed

### Scrum vs Kanban Support
All personas support both methodologies:
- **Scrum**: Sprint-based metrics, velocity, sprint goals
- **Kanban**: Flow-based metrics, WIP limits, cycle time

Users can toggle between modes to match their team's workflow.

---

## Future Enhancements

### PO Enhancements
- [ ] Roadmap view (timeline visualization)
- [ ] Release planning tools
- [ ] Risk/dependency heatmaps
- [ ] Export to PowerPoint/PDF

### Dev Enhancements
- [ ] Bi-directional sync (Jira → GitHub)
- [ ] Auto-create branches from tickets
- [ ] PR template integration
- [ ] Code review reminders

### SM Enhancements
- [ ] Predictive analytics (forecasting)
- [ ] Team capacity planning
- [ ] Retrospective insights
- [ ] Custom report builder
