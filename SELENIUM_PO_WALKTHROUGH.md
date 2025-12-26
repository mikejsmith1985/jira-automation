# 🎯 PO User Flow: How Selenium Works in Waypoint

## The Scenario
You're a **Product Owner (PO)** and you want to see your features tracked in Waypoint. Here's **exactly what happens** with Selenium behind the scenes.

---

## Step-by-Step Walkthrough

### **STEP 1: You Launch the App**

**What you do:**
- Double-click `GitHubJiraSync.exe` (or run `python app.py`)

**What happens behind the scenes:**

```python
# app.py - Lines 214-230
def handle_init(self, data):
    """Initialize browser"""
    global driver
    
    # Initialize Chrome WebDriver if not already done
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        # Hide automation markers so Jira doesn't block us
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # This is the KEY line - Selenium launches Chrome browser
        driver = webdriver.Chrome(options=chrome_options)  # 🚀 Chrome launches!
    
    # Initialize sync engine with the driver
    if sync_engine is None:
        sync_engine = SyncEngine(driver)
    
    # Navigate to Jira for authentication
    jira_url = "https://your-company.atlassian.net"
    driver.get(jira_url)  # 🌐 Opens Jira in the Chrome browser
```

**Visual representation:**
```
┌─────────────────────────────────────┐
│  Waypoint App (HTTP Server)         │
│  http://localhost:5000              │
└──────────────────┬──────────────────┘
                   │ Creates
                   ▼
        ┌──────────────────┐
        │  Selenium Driver │
        │  (Python Object) │
        └──────────────────┘
                   │ Controls
                   ▼
        ┌──────────────────┐
        │  Chrome Browser  │
        │  (Actual Window) │
        └──────────────────┘
                   │ 
                   ▼ Navigates to
        ┌──────────────────────────────┐
        │  Jira: https://your-company  │
        │  Waits for YOU to log in     │
        └──────────────────────────────┘
```

---

### **STEP 2: You Log In to Jira**

**What you do:**
- Jira opens in the Chrome browser (controlled by Selenium)
- You enter your username/password
- You click login

**What Selenium sees:**
```python
# Selenium is watching the Chrome browser
# It can see that the HTML changed from:
# <form class="login"> ... </form>
# 
# To:
# <div class="dashboard"> ... </div>
#
# This means you've successfully logged in!
```

**Why this matters:**
- Selenium doesn't actually log in FOR you
- Instead, you authenticate manually once
- Selenium then **remembers your session** (cookies stay in the Chrome browser)
- All future requests use the same authenticated Chrome browser

---

### **STEP 3: You Configure Waypoint Settings**

**What you do (in the Waypoint UI):**
1. Click the ⚙️ **Settings** tab
2. Enter:
   - **Jira URL:** `https://your-company.atlassian.net`
   - **Jira Project Key:** `MYPROJ`
   - **GitHub Organization:** `my-company`
3. Click **Save**

**What happens:**

```yaml
# config.yaml - Gets saved
jira:
  base_url: "https://your-company.atlassian.net"
  project_key: "MYPROJ"

github:
  organization: "my-company"
  repositories:
    - "repo-1"
    - "repo-2"
```

---

### **STEP 4: You Click "PO" Tab (Features View)**

**What you do:**
- Click the 👔 **PO** tab in Waypoint

**What you see:**
- Empty state message: "No features loaded. Import Jira data to view features and epics"

**What Selenium is doing:**
```python
# The PO tab is mostly for VISUALIZATION
# It expects you to provide data in one of these ways:

# Option 1: Upload a JSON file with your features
# Example structure:
{
  "epics": [
    {
      "key": "MYPROJ-100",
      "name": "User Authentication",
      "status": "In Progress",
      "children": [
        {
          "key": "MYPROJ-101",
          "name": "Login Form",
          "status": "Done",
          "assignee": "john@company.com"
        }
      ]
    }
  ]
}

# Option 2: Selenium can scrape this from Jira if you enable it
# (But currently this requires manual data upload)
```

---

### **STEP 5: You Want to See Features - Now Selenium Actually Works!**

**The DEV tab is where Selenium automatically syncs GitHub → Jira**

Let's say you click the 💻 **Dev** tab and it shows:
- "0 PRs Synced"
- "0 Tickets Updated"

**What you then do:**
1. Click **"Enable Automation"**
2. Click **"Sync Now"** button

**What happens (THE SELENIUM MAGIC):**

```python
# app.py - handle_sync_now()
def handle_sync_now(self):
    """Run sync immediately"""
    sync_engine.sync_once()  # 🚀 This is where Selenium kicks in!

# sync_engine.py - sync_once()
def sync_once(self):
    """Run a single sync cycle"""
    
    # Step A: GitHub gets your recent PRs
    prs = self.github.get_recent_prs("my-company/repo-1", hours_back=24)
    # Result: [
    #   {
    #     "number": 456,
    #     "title": "Add login validation",
    #     "branch": "feature/auth-form",
    #     "body": "Fixes MYPROJ-101"  # ⭐ Jira ticket in commit message!
    #   }
    # ]
    
    # Step B: For each PR, update the Jira ticket
    for pr in prs:
        updated_count = self._process_pr(pr)  # 🤖 Selenium works here!
```

**Now here's where SELENIUM takes over and actually interacts with Jira:**

```python
# jira_automator.py - update_ticket()
def update_ticket(self, ticket_key, updates):
    """Update a Jira ticket using Selenium"""
    
    # STEP 1: Navigate to the ticket
    ticket_url = f"{self.base_url}/browse/MYPROJ-101"
    self.driver.get(ticket_url)  # 🌐 Opens: https://company.atlassian.net/browse/MYPROJ-101
    time.sleep(2)  # Wait for page to load
    
    # STEP 2: Add a comment
    # Selenium finds the comment box element on the page
    comment_box = self.driver.find_element(By.ID, "comment")
    comment_box.send_keys("✅ PR #456 merged: Add login validation")
    
    # STEP 3: Click the save button
    save_button = self.driver.find_element(By.CLASS_NAME, "button-save")
    save_button.click()  # 👆 Selenium literally clicks the button!
    
    # STEP 4: Add a label
    # Selenium finds the label field
    label_field = self.driver.find_element(By.ID, "labels-input")
    label_field.send_keys("pr-merged\n")  # Type label and press enter
    
    # STEP 5: Update status (optional)
    # Selenium finds the status dropdown
    status_dropdown = self.driver.find_element(By.ID, "status")
    status_dropdown.click()
    
    # Find and click "In Review" option
    in_review_option = self.driver.find_element(By.XPATH, "//span[text()='In Review']")
    in_review_option.click()
```

---

## Visual Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      YOU (Product Owner)                         │
└──────────────────────────────────────────────────────────────────┘
                           ▲
                           │ You see in browser
                           │
┌──────────────────────────────────────────────────────────────────┐
│                   Waypoint Web UI                                │
│              http://localhost:5000                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Dashboard   │ │ PO (Viz)    │ │ Dev (Sync)  │                │
│  │  (Shows     │ │ (Shows      │ │ (Shows PR   │                │
│  │   Status)   │ │  Features)  │ │  Sync)      │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
└──────────────────────────────────────────────────────────────────┘
                           ▲
                           │ HTTP Requests/Responses
                           │
┌──────────────────────────────────────────────────────────────────┐
│              Python Backend (app.py)                             │
│     ┌────────────────────────────────────────┐                  │
│     │ SyncEngine                             │                  │
│     │ - Orchestrates everything              │                  │
│     │ - Has reference to driver (Selenium)   │                  │
│     └────────────────────────────────────────┘                  │
│               ▲              ▲                                   │
│               │              │                                   │
│      ┌────────▼────┐   ┌─────▼─────────┐                        │
│      │ GitHub API  │   │ JiraAutomator │                        │
│      │ Scraper     │   │ (Uses Selenium)                        │
│      └─────────────┘   └─────┬─────────┘                        │
└───────────────────────────────┼────────────────────────────────┘
                                │ Uses
                                │
                    ┌───────────▼──────────┐
                    │  Selenium WebDriver  │
                    │  (Python Object)     │
                    └───────────┬──────────┘
                                │ Controls
                                │
                    ┌───────────▼──────────┐
                    │   Chrome Browser     │
                    │  (Actual GUI Window) │
                    └───────────┬──────────┘
                                │ Navigates to
                                │
                    ┌───────────▼─────────────────┐
                    │ Jira Instance               │
                    │ https://company.atlassian   │
                    │                             │
                    │ - Reads ticket details      │
                    │ - Updates tickets           │
                    │ - Adds comments             │
                    │ - Changes status            │
                    │ - Adds labels               │
                    └─────────────────────────────┘
```

---

## The KEY Insight: WHY Selenium?

**The Problem:**
- Jira has NO public API that allows ticket updates (in this architecture)
- We can't use REST API calls to change tickets
- We need to interact with Jira just like a human would

**The Solution: Selenium**
- Launches a real Chrome browser
- Navigates to Jira
- Finds HTML elements (buttons, fields, etc.)
- Clicks them, types in them, submits forms
- **This is indistinguishable from a human doing it manually**
- Jira never knows it's automated!

---

## Complete PO User Journey

```
START: You double-click Waypoint.exe
   │
   ├─→ ✅ Step 1: Selenium launches Chrome browser
   │
   ├─→ ✅ Step 2: Chrome navigates to your Jira instance
   │
   ├─→ ✅ Step 3: You manually log in (human step - Selenium waits)
   │
   ├─→ ✅ Step 4: Waypoint UI loads at http://localhost:5000
   │
   ├─→ ✅ Step 5: You click "Dev" tab and click "Sync Now"
   │
   ├─→ ✅ Step 6: SyncEngine queries GitHub for recent PRs
   │
   ├─→ ✅ Step 7: For each PR, Selenium:
   │      ├─ Opens the Jira ticket URL
   │      ├─ Finds the comment field
   │      ├─ Types a comment about the PR
   │      ├─ Clicks save
   │      ├─ Finds the labels field
   │      ├─ Adds "pr-merged" label
   │      └─ Updates ticket status
   │
   ├─→ ✅ Step 8: You see "5 PRs Synced" in the UI
   │
   └─→ END: Jira tickets are now updated with PR information!
```

---

## For the PO Persona Specifically

**What PO Features Use Selenium:**
1. ❌ **Features & Epics View** - Does NOT use Selenium (you upload data)
2. ❌ **Dependency Canvas** - Does NOT use Selenium (you upload data)
3. ✅ **Team Metrics** - Optional Selenium to scrape metrics from Jira

**What PO Features Are Manual:**
- Uploading feature data as JSON
- Viewing and exporting reports
- Toggling between Scrum/Kanban views

**What USES Selenium (for Dev Persona, but affects PO):**
- Syncing GitHub PRs to Jira tickets
- This updates Jira, which affects your overall project status

---

## The Session Lifecycle

```
1. App Starts
   └─→ Selenium creates Chrome browser instance
   └─→ Browser stores session cookies

2. You Log In
   └─→ You manually authenticate in Chrome
   └─→ Session cookie is saved in browser
   └─→ Selenium can now access Jira as you

3. You Click "Sync Now"
   └─→ Selenium uses the SAME browser session
   └─→ It's as if you're clicking buttons yourself
   └─→ Jira sees requests from YOUR browser session

4. You Close the App
   └─→ Selenium quits the Chrome process
   └─→ Browser instance destroyed
   └─→ Session ends

Next time you open the app:
   └─→ A NEW Chrome browser instance starts
   └─→ You need to log in again
   └─→ New session is created
```

---

## Summary: What Happens When You Use Waypoint as a PO

1. **You launch the app** → Selenium quietly launches Chrome
2. **You log in to Jira** → Selenium watches and remembers
3. **You configure settings** → Saved to `config.yaml`
4. **You click "Sync Now"** → Selenium takes over Jira:
   - Opens your tickets
   - Updates fields
   - Adds comments with PR links
   - Changes statuses
   - Adds labels
5. **Your features are updated** → You can now see PR status in Jira!

**The magic:** Selenium lets Waypoint automate all the manual Jira clicking that would normally take hours, without needing a REST API. It's like having a robot assistant that knows exactly where to click in Jira!
