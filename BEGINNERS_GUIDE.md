# 🎓 GitHub-Jira Sync Tool - Beginner's Guide

**Welcome!** This document explains how every file in this application works, written for someone who's new to programming.

## 📚 Table of Contents

1. [What Does This App Do?](#what-does-this-app-do)
2. [How All The Files Work Together](#how-all-the-files-work-together)
3. [Individual File Explanations](#individual-file-explanations)
4. [How To Use The App](#how-to-use-the-app)
5. [Customizing For Your Needs](#customizing-for-your-needs)

---

## What Does This App Do?

Imagine you're a teacher with two different notebooks:
- **Notebook 1 (GitHub)**: Where students submit their homework
- **Notebook 2 (Jira)**: Where you track which homework needs grading

Every time a student submits homework, you have to:
1. Look at Notebook 1
2. Write in Notebook 2: "Student submitted homework"
3. Maybe update the grade when they fix it
4. Mark it "Done" when everything's complete

**This app does all that automatically!** It watches GitHub (Notebook 1) and updates Jira (Notebook 2) for you.

### Real Example:

1. Developer creates Pull Request "ABC-123: Fix login bug"
2. App sees "ABC-123" in the PR title
3. App finds ticket ABC-123 in Jira
4. App adds comment: "PR opened: https://github.com/..."
5. App adds label "has-pr"
6. When PR is merged, app changes ticket to "Done"

---

## How All The Files Work Together

Think of this app like a restaurant kitchen:

```
config.yaml
└─ The Recipe Book
   Tells everyone what to make and when

app.py
└─ The Head Chef
   Takes orders from the waiter (web browser)
   Tells other chefs what to do

sync_engine.py
└─ The Kitchen Manager
   Schedules when things happen
   Makes sure all chefs work together

github_scraper.py
└─ The Prep Cook
   Goes to GitHub
   Finds all the Pull Requests
   Brings back the information

jira_automator.py
└─ The Line Cook
   Goes to Jira
   Updates tickets
   Adds comments and changes fields

requirements.txt
└─ The Shopping List
   Lists all the ingredients (Python libraries) we need

build.ps1
└─ The Packaging System
   Wraps everything into one file (.exe)
```

### The Flow (Like an Assembly Line):

```
1. ⏰ SCHEDULER (sync_engine.py)
   "It's 9:00 AM! Time to check for updates"
   ↓

2. 🔍 GITHUB SCRAPER (github_scraper.py)
   "I found 5 new PRs!"
   ↓

3. 🧠 SYNC ENGINE (sync_engine.py)
   "PR #1 has ticket ABC-123, let me update it"
   ↓

4. ✏️ JIRA AUTOMATOR (jira_automator.py)
   "Opening ABC-123... adding comment... done!"
   ↓

5. 📊 LOGGING
   "Updated 5 tickets successfully"
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
