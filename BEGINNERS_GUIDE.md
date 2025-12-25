# 🎓 GitHub-Jira Sync Tool - Complete Architectural Guide

**Purpose:** This document explains how every component in the application works and how they fit together. Perfect for understanding the system before diving into code.

## 📚 Table of Contents

1. [What Does This App Do?](#what-does-this-app-do)
2. [The Three Personas](#the-three-personas)
3. [How All Components Work Together](#how-all-components-work-together)
4. [Individual Component Explanations](#individual-component-explanations)
5. [Data Flow: From Trigger to Jira Update](#data-flow-from-trigger-to-jira-update)
6. [The Feedback System](#the-feedback-system)
7. [Configuration & Customization](#configuration--customization)

---

## What Does This App Do?

Imagine you manage two different systems:
- **System 1 (GitHub):** Where developers submit code changes (Pull Requests)
- **System 2 (Jira):** Where you track work items and status

Every time something happens in GitHub, you have to manually update Jira:
1. "A PR was opened for feature X"
2. "The PR got merged, so mark ticket X as done"
3. "A PR had a review comment, add that feedback to the ticket"

**This app automates all of that.** It watches GitHub and automatically updates Jira tickets for you.

### Real-World Example:

1. Developer creates Pull Request: "ABC-123: Fix login bug"
2. App sees "ABC-123" in the PR title
3. App finds ticket ABC-123 in Jira
4. App adds comment: "PR opened: https://github.com/org/repo/pull/456"
5. App adds label "has-pr"
6. Developers review and approve
7. PR gets merged
8. App moves ticket ABC-123 to "Done" status automatically
9. No manual work needed! ✨

---

## The Three Personas

This app serves three different types of users with different goals:

### 👔 **Product Owner (PO) - The Planner**
**Goal:** Visualize features and track progress for decision-making

**What they need:**
- "Which features are blocked?"
- "What's the status of our Q1 roadmap?"
- "What dependencies are blocking us?"
- "Can we ship this release?"

**Features:**
- **Features & Epics View** - See all features with child issues and progress bars
- **Dependency Canvas** - Visual map of how issues block each other
- **Export Reports** - Download data for presentations

**Data source:** Manual upload of feature structures (JSON/YAML)

---

### 💻 **Developer (Dev) - The Automator**
**Goal:** Reduce manual work by automating Jira updates from GitHub

**What they need:**
- "Every PR should link to the Jira ticket"
- "When a PR is merged, mark the ticket done"
- "Run our sync every hour automatically"

**Features:**
- **Multi-Workflow System** - Define different rules for different scenarios
- **Flexible Scheduling** - Run hourly, daily, or weekly
- **Favorites** - Save common tasks for one-click execution
- **Multiple Updates** - Update fields, labels, status all at once

**Data source:** GitHub PRs (scraped via Selenium)

---

### 📊 **Scrum Master (SM) - The Health Monitor**
**Goal:** Identify team issues and track team health metrics

**What they need:**
- "How is our velocity trending?"
- "Are we stalling on any work?"
- "Do we have scope creep?"
- "What tickets need attention?"

**Features:**
- **Insights Engine** - Automatic detection of problems (scope creep, defects, stale work)
- **Team Health Metrics** - Velocity, cycle time, WIP, burndown
- **Hygiene Checks** - Missing estimates, long-running stories, blockers
- **Trend Analysis** - See velocity and cycle time changes over time
- **Persistent Storage** - Historical data in SQLite database

**Data source:** Jira data (scraped via Selenium) + GitHub PRs

---

## How All Components Work Together

Think of the application like a restaurant kitchen with specialized chefs:

```
┌─────────────────────────────────────────────────┐
│              WEB INTERFACE (app.py)              │
│  • User selects their persona                   │
│  • Configures workflows and settings            │
│  • Views insights and reports                   │
│  • Submits feedback via floating bug button     │
└────────┬────────────────────────────┬───────────┘
         │                            │
    HTTP Requests              HTTP Requests
         │                            │
┌────────▼──────────┐        ┌───────▼────────────┐
│  SCHEDULER/RUNNER │        │  GITHUB FEEDBACK   │
│  (sync_engine.py)│        │  (github_feedback) │
└────────┬──────────┘        └────────────────────┘
         │
    Coordinates Work
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌──────────────────────┐   ┌──────────────────────┐
│  GITHUB SCRAPER      │   │  JIRA AUTOMATOR      │
│  (github_scraper.py) │   │  (jira_automator.py) │
│                      │   │                      │
│ • Opens GitHub       │   │ • Opens Jira tickets │
│ • Finds PRs          │   │ • Updates fields     │
│ • Extracts metadata  │   │ • Adds comments      │
│ • Returns PR list    │   │ • Changes status     │
└──────────────────────┘   │ • Adds labels        │
                           └──────────────────────┘
    Selenium WebDriver (Browser Automation)
         │
         ▼
    ┌──────────────────────────────┐
    │   Chrome/Chromium Browser    │
    │  (User watches automation!)  │
    └──────────────────────────────┘

┌─────────────────────────────────────────────────┐
│           INSIGHTS & STORAGE                    │
│  • insights_engine.py (pattern detection)       │
│  • feedback_db.py (SQLite database)             │
│  • Historical metrics and insights              │
└─────────────────────────────────────────────────┘
```

### The Flow in Action:

**Scenario:** Developer creates PR "ABC-123: Fix login bug"

```
1. 🕐 SCHEDULER (sync_engine.py)
   └─> "It's 9:00 AM! Time to check GitHub for new PRs"

2. 🔍 GITHUB SCRAPER (github_scraper.py)
   └─> Opens GitHub in browser
   └─> Finds PR #456: "ABC-123: Fix login bug"
   └─> Extracts: title, URL, author, status
   └─> Returns to scheduler

3. 🧠 SYNC ENGINE (sync_engine.py)
   └─> "I found ticket ABC-123 in the PR title"
   └─> "What should I do? Let me check config.yaml"
   └─> "PR opened → add comment, add label, set field"

4. ✏️ JIRA AUTOMATOR (jira_automator.py)
   └─> Opens ABC-123 in Jira
   └─> Adds comment: "PR opened: https://github.com/..."
   └─> Adds label: "has-pr"
   └─> Updates PR Link field
   └─> Saves

5. 📊 LOGGING & INSIGHTS
   └─> Records: "Updated ABC-123 successfully"
   └─> Stores metrics in SQLite
   └─> Updates team velocity stats

✅ Done! All automated, no manual work!
```

---

## Individual Component Explanations

### **app.py - The Web Server & UI**

**Purpose:** HTTP server that provides the web interface and API

**What it does:**
- Starts a Python HTTP server on localhost:5000
- Serves embedded HTML/CSS/JavaScript to browser
- Handles user interactions (clicks, form submissions)
- Routes requests to appropriate handlers
- Manages global state (driver, sync_engine, database connections)
- Provides REST API endpoints

**Key Sections:**
```python
# The HTTP request handler class
class SyncHandler(BaseHTTPRequestHandler):
    def do_GET(self):    # Handle GET requests (fetch page, config, status)
    def do_POST(self):   # Handle POST requests (init, sync, save config)

# API Endpoints
/api/init              # Initialize browser
/api/sync-now          # Run sync immediately
/api/start-scheduler   # Start scheduled syncs
/api/config            # Get/save configuration
/api/insights          # Get insights
/api/feedback/submit   # Submit feedback to GitHub
```

**Why separate file?** Because it's the "waiter" that takes orders from the user and tells other components what to do.

---

### **sync_engine.py - The Orchestrator**

**Purpose:** Coordinates all the work and schedules when things happen

**What it does:**
- Loads configuration from config.yaml
- Initializes GitHubScraper and JiraAutomator
- Runs sync cycles (one-time or scheduled)
- Processes each PR found
- Matches PRs to Jira tickets
- Calls JiraAutomator to update tickets
- Logs everything to file and database
- Handles scheduling (hourly, daily, weekly)

**Key Methods:**
```python
sync_once()              # Run a single sync cycle
_process_pr(pr)          # Process one PR
start_scheduled()        # Start running on schedule
```

**Why separate file?** Because the scheduling and orchestration logic is complex and should be independent from the web UI.

---

### **github_scraper.py - The GitHub Reader**

**Purpose:** Extracts Pull Request information from GitHub

**How it works:**
1. Opens GitHub.com in the browser (via Selenium)
2. Navigates to the Pull Requests page for a specific repository
3. Finds all PR elements on the page
4. Extracts from each PR: title, URL, author, status, branch name
5. Looks for Jira ticket keys in the PR title (like "ABC-123")
6. Returns a list of PR dictionaries

**Why Selenium instead of GitHub API?**
- The team doesn't have GitHub API access yet
- Selenium works like a human visiting the page
- Can scrape any GitHub.com page without authentication issues

**Key Methods:**
```python
get_recent_prs(repo_name, hours_back=24)  # Get PRs updated in last X hours
get_pr_details(pr_url)                     # Get detailed info about one PR
```

**Example Output:**
```python
{
    'repo': 'my-awesome-app',
    'number': '456',
    'title': 'ABC-123: Fix login bug',
    'url': 'https://github.com/org/my-awesome-app/pull/456',
    'status': 'merged',  # or 'open' or 'closed'
    'author': 'john_doe',
    'branch': 'feature/ABC-123-fix-login',
    'ticket_keys': ['ABC-123']  # Jira keys found in title
}
```

---

### **jira_automator.py - The Jira Updater**

**Purpose:** Updates Jira tickets via browser automation

**How it works:**
1. Opens a Jira ticket in the browser
2. Finds the comment box
3. Types the comment message
4. Clicks save
5. Updates custom fields (like PR link)
6. Adds labels
7. Changes ticket status
8. All done! ✨

**Why this approach?**
- No Jira API access available
- Selenium can click buttons just like a human would
- Works with any Jira configuration

**Key Methods:**
```python
update_ticket(ticket_key, updates)  # Main method: does all updates
_add_comment(text)                  # Add comment to ticket
_update_fields(fields)              # Update custom fields
_add_labels(labels)                 # Add labels to ticket
_set_status(status)                 # Change ticket status
```

**Example Usage:**
```python
jira.update_ticket('ABC-123', {
    'comment': '🔗 PR opened: https://github.com/...',
    'fields': {
        'customfield_10001': 'https://github.com/org/repo/pull/456'
    },
    'labels': ['has-pr', 'in-review'],
    'status': 'In Review'
})
```

---

### **insights_engine.py - The Pattern Detector**

**Purpose:** Automatically detects team issues without needing AI/LLM

**What it detects:**
- **Scope Creep** - Stories growing by >30% after sprint start
- **Defect Leakage** - Production bugs escaping QA (>20% alert)
- **Velocity Trends** - Significant velocity changes (±15%)
- **Stale Tickets** - No updates in 14+ days
- **Missing Estimates** - Stories without story points
- **Long Runners** - Stories in progress >10 days
- **Blocked Items** - Stories stuck in a status

**How it works:**
1. Takes Jira data as input (usually scraped)
2. Runs rule-based checks (no AI/LLM)
3. Generates insights with severity levels
4. Stores in SQLite database
5. Returns to UI for display

**Example Rule (Scope Creep):**
```python
if story['story_points'] > story['initial_story_points'] * 1.3:
    # Growth > 30%
    insight = {
        'type': 'scope_creep',
        'severity': 'warning',
        'message': f"Story {key} grew from {initial} to {current} points"
    }
```

---

### **feedback_db.py - The Data Vault**

**Purpose:** Stores insights, metrics, and logs in SQLite

**What it stores:**
- Team insights (scope creep, defects, etc.)
- Historical metrics (velocity per sprint, cycle time trends)
- Application logs (sync runs, errors, user actions)
- Feedback entries (user-submitted bug reports)

**Why SQLite?**
- No server needed (just a file)
- Can query historical data
- Persists across app restarts
- Lightweight and fast

**Database Tables:**
```
insights          - Detected team issues
metrics_history   - Historical velocity, cycle time, WIP
logs              - Application operation logs
feedback          - User-submitted feedback
```

---

### **github_feedback.py - The Feedback System**

**Purpose:** Captures logs, screenshots, video and submits issues to GitHub

**What it captures:**
- **Console Logs** - All JavaScript console.log/console.error calls
- **Network Errors** - Failed API requests and network failures
- **Screenshots** - Full page screenshot at time of feedback
- **Video** - 30-second screen recording of browser tab
- **System Info** - Browser, OS, app version

**How it works:**
1. User clicks 🐛 bug button in corner
2. Feedback modal opens
3. User enters title and description
4. User optionally captures screenshot or video
5. System auto-captures console logs (last 5 minutes)
6. User clicks submit
7. Submits GitHub issue via GitHub API with all attachments
8. Issue created with logs, screenshot, video as comments

**Why important?**
- Users can report bugs without leaving the app
- We get rich diagnostic data (logs, screenshots, video)
- All issues go to one place (GitHub)
- Privacy-focused (browser tab only, not full screen)

---

### **config.yaml - The Configuration File**

**Purpose:** Centralized configuration for all workflows, settings, and mappings

**What it contains:**

```yaml
github:
  base_url: "https://github.com"
  organization: "your-org"  # Your GitHub org
  repositories: ["repo1", "repo2"]

jira:
  base_url: "https://your-company.atlassian.net"
  project_keys: ["PROJ", "ABC"]
  custom_fields:
    pr_link: "customfield_10001"  # Maps field names to IDs

workflows:
  pr_sync:
    enabled: true
    schedule:
      frequency: "hourly"
      business_hours_only: true
    pr_opened:
      add_comment: true
      labels: ["has-pr"]
      set_status: ""  # Don't change status

favorites:
  favorite_1:
    name: "Update PR Links"
    jql_query: "status = 'In Review' AND 'PR Link' is EMPTY"
    updates:
      fields:
        pr_link: "https://github.com/..."
```

**Why separate file?**
- Users can customize without editing Python code
- Easy to enable/disable workflows
- Portable across machines
- Non-technical users can update it

---

## Data Flow: From Trigger to Jira Update

Let's trace what happens when a developer opens a PR:

```
1️⃣  GITHUB EVENT
    └─> Developer creates PR: "ABC-123: Fix login"
    └─> PR is now at: https://github.com/org/repo/pull/456

2️⃣  SCHEDULER TRIGGER (sync_engine.py)
    └─> Scheduled time arrives (e.g., hourly)
    └─> Calls: sync_engine.sync_once()

3️⃣  GITHUB SCRAPING (github_scraper.py)
    └─> Opens GitHub in Selenium browser
    └─> Navigates to: https://github.com/org/repo/pulls
    └─> Finds PR row in HTML table
    └─> Extracts: title, status, author, URL, branch
    └─> Regex search in title: "ABC-123"
    └─> Returns to sync_engine

4️⃣  TICKET MATCHING (sync_engine.py)
    └─> Ticket key found: "ABC-123"
    └─> Looks up workflow rules in config.yaml
    └─> Event: "pr_opened"
    └─> Gets actions: add comment, add label, update field

5️⃣  JIRA UPDATE (jira_automator.py)
    └─> Navigates to: https://jira.com/browse/ABC-123
    └─> Adds comment: "🔗 PR opened: https://github.com/..."
    └─> Adds label: "has-pr"
    └─> Updates field: "customfield_10001" = "https://github.com/..."
    └─> Saves all changes

6️⃣  LOGGING & METRICS (feedback_db.py)
    └─> Records in SQLite:
    └─> "Updated ABC-123: comment, label, field"
    └─> Timestamp: 2025-12-25 09:15:00
    └─> Status: success

7️⃣  INSIGHTS CHECK (insights_engine.py)
    └─> Analyzes team metrics
    └─> Updates velocity, WIP, cycle time
    └─> Detects any issues
    └─> Stores in SQLite

✅ COMPLETE
   └─> User sees "Sync successful" in web UI
   └─> Can view logs and metrics on SM tab
```

---

## The Feedback System

The floating 🐛 bug button provides a way for users to report issues with rich diagnostic data:

### Flow:
1. User clicks bug button → Modal opens
2. User enters title: "Canvas not loading"
3. User enters description: "When I upload JSON, nothing happens"
4. User clicks "Capture Screenshot" → Page screenshot taken
5. User clicks "Record Video" → 30s browser recording
6. User clicks "Submit" → GitHub issue created with:
   - Title and description
   - Automatically captured logs (Python + browser)
   - Screenshot (as PNG attachment)
   - Video (as MP4/WebM attachment)
   - System info (browser, OS, app version)
7. Issue appears in GitHub repo
8. Developer can investigate with full diagnostic context

### Why this approach?
- **Privacy:** Records browser tab only, not full screen
- **Rich Diagnostics:** Logs + screenshot + video = easy to debug
- **Low Friction:** Built into app, users don't leave to report issues
- **Centralized:** All feedback in GitHub Issues

---

## Configuration & Customization

### Adding a New Workflow

In `config.yaml`:
```yaml
workflows:
  daily_label_cleanup:
    enabled: true
    description: "Remove old labels from closed tickets"
    schedule:
      frequency: "daily"
      time: "08:00"
    jql_query: "status = Closed AND labels = 'needs-review'"
    updates:
      comment_template: "Removing stale labels"
      labels: []  # (Could remove labels if function added)
      set_status: ""
```

### Adding a Custom Field Mapping

In `config.yaml`:
```yaml
jira:
  custom_fields:
    pr_link: "customfield_10001"
    fix_version: "customfield_10002"
    reviewer: "customfield_10003"  # New field!
```

Then use in workflow updates:
```yaml
pr_opened:
  fields:
    pr_link: "{pr_url}"
    reviewer: "{author}"  # Set reviewer to PR author
```

### Extending with New Rules

In `insights_engine.py`, add a new detection rule:
```python
def detect_bottleneck(self, jira_data):
    """Detect when one team member has too much work"""
    for assignee in get_assignees(jira_data):
        open_count = count_open_by_assignee(assignee, jira_data)
        if open_count > 10:
            return {
                'type': 'bottleneck',
                'severity': 'warning',
                'assignee': assignee,
                'open_count': open_count
            }
```

---

## Summary: The Big Picture

```
USER (Browser)
   ↓
Web UI (app.py)
   ↓
Orchestration (sync_engine.py)
   ├─→ Read from GitHub (github_scraper.py)
   ├─→ Write to Jira (jira_automator.py)
   ├─→ Detect patterns (insights_engine.py)
   ├─→ Store data (feedback_db.py)
   └─→ Submit feedback (github_feedback.py)
   ↓
Browser (Selenium) ← Automates clicking/typing
   ↓
Jira & GitHub (Actual systems updated)
```

**Key principle:** Separate concerns into modules, each with one clear responsibility. The orchestrator (sync_engine) ties them all together based on configuration.

---

## Next Steps to Understand Better

1. **Read the source code** - Start with `app.py` main function
2. **Trace a workflow** - See what happens when you click "Run Sync"
3. **Check the logs** - Understand what each component logs
4. **Run in debug mode** - Add print statements to see data flow
5. **Customize a workflow** - Add your own workflow to config.yaml
6. **Write a test** - Try updating a test Jira ticket manually

---

**Built with:** Selenium WebDriver + Python HTTP server + SQLite + GitHub API

**No dependencies on:** Jira API, GitHub API (optional), cloud services

**Fully self-contained:** Runs on one machine, no external services required ✨
```

---

## Individual File Explanations

### 1. `config.yaml` - The Settings File

**What it does**: Stores all your settings in one place

**Think of it like**: A settings menu in a video game

**Contains**:
- Your GitHub organization name
- Your Jira URL
- When to run (every hour? every day?)
- What to do when PRs are opened/merged/closed
- Custom workflows for different scenarios

**Example**:
```yaml
github:
  organization: "my-company"
  
workflows:
  pr_sync:
    pr_opened:
      add_comment: true
      comment_template: "PR opened: {pr_url}"
```

**In plain English**: "When a PR is opened, add a comment that says 'PR opened: [link]'"

---

### 2. `app.py` - The Web Interface

**What it does**: Creates a web page where you can control the app

**Think of it like**: The control panel for a robot

**Main parts**:

#### A. The Web Server
```python
def run_server():
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, SyncHandler)
    httpd.serve_forever()
```
**Translation**: "Create a web server on your computer at http://localhost:5000"

#### B. Handling Requests
```python
def handle_init(self, data):
    driver = webdriver.Chrome()
    sync_engine = SyncEngine(driver)
```
**Translation**: "When user clicks 'Initialize', open Chrome and get ready to work"

#### C. Running Sync
```python
def handle_sync_now(self):
    sync_engine.sync_once()
```
**Translation**: "When user clicks 'Sync Now', do a sync right now"

**Why you need it**: So you can control the app without typing code

---

### 3. `sync_engine.py` - The Brain

**What it does**: Orchestrates (coordinates) everything

**Think of it like**: A conductor for an orchestra - makes sure everyone plays at the right time

**Main functions**:

#### A. Load Configuration
```python
with open('config.yaml', 'r') as f:
    self.config = yaml.safe_load(f)
```
**Translation**: "Read the settings from config.yaml"

#### B. Run One Sync Cycle
```python
def sync_once(self):
    prs = self.github.get_recent_prs()
    for pr in prs:
        ticket_keys = extract_keys(pr.title)
        for key in ticket_keys:
            self.jira.update_ticket(key, updates)
```
**Translation**: 
1. "Get list of PRs from GitHub"
2. "For each PR, find ticket keys (like ABC-123)"
3. "For each ticket, update it in Jira"

#### C. Schedule Regular Runs
```python
def start_scheduled(self):
    for hour in range(9, 18):
        schedule.every().day.at(f"{hour}:00").do(self.sync_once)
```
**Translation**: "Run sync_once() every hour from 9 AM to 6 PM"

**Why you need it**: Connects GitHub and Jira together automatically

---

### 4. `github_scraper.py` - The GitHub Inspector

**What it does**: Looks at GitHub and finds Pull Requests

**Think of it like**: A detective looking for clues

**Main functions**:

#### A. Get Recent PRs
```python
def get_recent_prs(self, repo_name):
    url = f"{self.base_url}/{self.org}/{repo_name}/pulls"
    self.driver.get(url)
    pr_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[id^="issue_"]')
```
**Translation**:
1. "Go to the Pull Requests page"
2. "Find all the PR boxes on the page"

#### B. Extract PR Data
```python
title = title_elem.text
pr_url = title_elem.get_attribute('href')
ticket_keys = re.findall(pattern, title)
```
**Translation**:
1. "Get the PR title"
2. "Get the PR URL"
3. "Find ticket keys in the title (like ABC-123)"

**How it finds ticket keys**:
- PR title: "ABC-123: Fix login bug"
- Regex pattern: `([A-Z]+-\d+)`
- Finds: "ABC-123"

**Why you need it**: To know what PRs exist and which Jira tickets they relate to

---

### 5. `jira_automator.py` - The Jira Worker

**What it does**: Updates Jira tickets like a human would

**Think of it like**: A robot that knows how to use Jira

**Main functions**:

#### A. Update Ticket
```python
def update_ticket(self, ticket_key, updates):
    ticket_url = f"{self.base_url}/browse/{ticket_key}"
    self.driver.get(ticket_url)
    
    if updates.get('comment'):
        self._add_comment(updates['comment'])
    
    if updates.get('fields'):
        self._update_fields(updates['fields'])
```
**Translation**:
1. "Go to the ticket page (like ABC-123)"
2. "If there's a comment to add, add it"
3. "If there are fields to update, update them"

#### B. Add Comment
```python
def _add_comment(self, comment_text):
    comment_field = self.driver.find_element(By.ID, 'comment')
    comment_field.send_keys(comment_text)
    comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
```
**Translation**:
1. "Find the comment box"
2. "Type the comment"
3. "Press Ctrl+Enter to save"

#### C. Update Multiple Fields
```python
def _update_fields(self, fields):
    edit_btn = self.driver.find_element(By.ID, 'edit-issue')
    edit_btn.click()
    
    for field_id, value in fields.items():
        field = self.driver.find_element(By.ID, field_id)
        field.clear()
        field.send_keys(value)
    
    update_btn = self.driver.find_element(By.ID, 'edit-issue-submit')
    update_btn.click()
```
**Translation**:
1. "Click the Edit button"
2. "For each field, clear it and type new value"
3. "Click Update to save"

**Why you need it**: To actually make changes in Jira

---

### 6. `requirements.txt` - The Dependencies

**What it does**: Lists all the Python libraries we need

**Think of it like**: A shopping list for your program

**Contents**:
```
selenium==4.16.0      # Controls Chrome browser
pyinstaller==6.17.0   # Packages app into .exe
pyyaml==6.0.1         # Reads config.yaml
schedule==1.2.0       # Schedules when things run
requests==2.31.0      # Makes web requests
```

**Why you need it**: So Python knows what to install

---

### 7. `build.ps1` - The Packager

**What it does**: Turns all the Python files into one .exe file

**Think of it like**: Wrapping a gift - takes all the pieces and makes one neat package

**What it does**:
```powershell
pip install -r requirements.txt  # Install dependencies
pyinstaller --onefile app.py     # Package into .exe
```

**Why you need it**: So you can run the app without Python installed

---

## How To Use The App

### First Time Setup:

1. **Install Python** (if not installed)
   ```bash
   python --version  # Should show 3.10 or higher
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Edit config.yaml**
   - Change `github.organization` to your GitHub org
   - Change `jira.base_url` to your Jira URL
   - Update field IDs (customfield_10001, etc.)

4. **Run the app**
   ```bash
   python app.py
   ```

5. **Open browser** to http://localhost:5000

6. **Click "Initialize"** - This opens Chrome

7. **Log in to Jira** in the Chrome window

8. **Click "Sync Now"** or "Start Scheduler"

### Daily Use:

- **Option 1**: Let it run automatically (scheduler)
  - Just leave the app running
  - It syncs every hour during business hours

- **Option 2**: Run manually when needed
  - Open http://localhost:5000
  - Click "Sync Now"

---

## Customizing For Your Needs

### Adding a New Workflow:

1. Open `config.yaml`

2. Add a new workflow under `workflows:`:
```yaml
my_custom_workflow:
  enabled: true
  description: "What this workflow does"
  schedule:
    frequency: "daily"
    time: "10:00"
  jql_query: "your JQL here"
  updates:
    add_comment: true
    comment_template: "Your message"
    fields:
      customfield_12345: "some value"
    labels:
      - "my-label"
```

3. Restart the app

### Finding Jira Field IDs:

1. Open a Jira ticket
2. Click "Edit"
3. Right-click on a field
4. Click "Inspect" (or "Inspect Element")
5. Look for `id="customfield_XXXXX"`
6. Use that ID in config.yaml

### Testing Before Going Live:

1. Create a test ticket in Jira
2. Create a test PR in GitHub with the ticket key
3. Run "Sync Now"
4. Check if the ticket was updated correctly
5. If not, check the logs: `jira-sync.log`

---

## Common Problems & Solutions

### "Could not add comment"
**Problem**: Jira's HTML changed
**Solution**: Update selectors in `jira_automator.py`

### "No PRs found"
**Problem**: GitHub scraping failed
**Solution**: Check if you're logged into GitHub in the browser

### "Field not found"
**Problem**: Wrong field ID in config
**Solution**: Use inspect tool to find correct ID

### "Sync not running"
**Problem**: Scheduler not started
**Solution**: Make sure you clicked "Start Scheduler"

---

## Next Steps

1. Read through each .py file with the comments
2. Try changing small things in config.yaml
3. Run the app and watch what it does
4. Check the logs to see what's happening
5. Ask questions if anything is unclear!

---

**Remember**: Programming is like learning a language. At first, it looks like gibberish, but the more you read and practice, the more sense it makes. Take your time, experiment, and don't be afraid to break things (that's how you learn)!

Good luck! 🚀
