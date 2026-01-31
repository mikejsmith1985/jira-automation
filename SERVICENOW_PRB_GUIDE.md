# ServiceNow PRB to Jira - User Guide

## What This Feature Does

This feature helps you automatically create Jira tickets from ServiceNow Problem (PRB) tickets. Instead of manually copying information from ServiceNow to Jira, Waypoint does it for you with a few clicks.

## How It Works (Simple Explanation)

Think of it like a smart copy-paste assistant:

1. **You tell Waypoint where your ServiceNow is** (like giving it an address)
2. **You give it a PRB number** (like PRB0123456)
3. **Waypoint opens that PRB in ServiceNow** (using the browser that's already logged in)
4. **It reads all the important information** from the PRB ticket
5. **It shows you what it found** so you can review it
6. **You click a button to create Jira tickets** based on that information

## Step-by-Step Setup

### Step 1: Configure ServiceNow Connection

1. Click the **PO** tab in Waypoint
2. Scroll to the "ServiceNow → Jira" section
3. Click the **⚙️ Configure** button (this takes you to Integrations)
4. Find the "ServiceNow Integration" section
5. Enter your **ServiceNow URL** (example: `https://yourcompany.service-now.com`)
6. Enter your **Jira Project Key** (example: `PROJ` or `DEV`)
7. Click **💾 Save Configuration**

### Step 2: Make Sure You're Logged Into ServiceNow

⚠️ **Important**: Before using this feature, you need to be logged into ServiceNow in a browser that Waypoint can use.

- Waypoint will use the same browser session you're already logged into
- If you see a login screen, just log in to ServiceNow normally
- Waypoint doesn't store your password - it just uses your existing login

## How to Use It

### Creating Jira Tickets from a PRB

1. **Go to the PO tab** in Waypoint
2. **Enter the PRB number** (example: `PRB0123456`)
3. **Click "🔍 Validate PRB"**
   - Waypoint will open ServiceNow and read the PRB ticket
   - This takes about 5-10 seconds
   - You'll see the PRB details appear on screen
4. **Review the information**
   - Check that the title, description, and other details look correct
   - If the PRB has related incidents, you'll see them listed
5. **Click "✨ Create Jira Issues"**
   - Waypoint will create Jira tickets based on what it found
   - You'll see progress messages as it works
   - When done, you'll get links to the new Jira tickets

## What Information Gets Copied

Waypoint copies these fields from ServiceNow PRB to Jira:

- **PRB Number** → Appears in Jira ticket
- **Short Description** → Becomes the Jira summary/title
- **Full Description** → Becomes the Jira description
- **Configuration Item** → Shows what system/app is affected
- **Impact, Urgency, Priority** → Help set importance in Jira
- **Problem Category** → Tags the type of issue
- **Related Incidents** → Listed in Jira (if any)

## Behind the Scenes (Technical Details)

### How Waypoint Finds the PRB

When you click "Validate PRB":

1. Waypoint builds a URL like this:
   ```
   https://yourcompany.service-now.com/problem.do?sysparm_query=number=PRB0123456
   ```

2. It opens this URL in a browser (using Selenium WebDriver)

3. It waits for the page to load (up to 10 seconds)

4. It looks for specific fields on the ServiceNow form by their field IDs:
   - `problem.number` → PRB number
   - `problem.short_description` → Title
   - `problem.description` → Full description
   - `sys_display.problem.cmdb_ci` → Configuration item
   - `problem.impact` → Impact level
   - `problem.urgency` → Urgency level
   - `problem.priority` → Priority level
   - `problem.u_problem_category` → Category
   - `problem.u_dectection` → How it was detected

5. It reads the values from these fields using browser automation

6. It also looks for related incidents by finding the "Incidents" related list

### How Jira Tickets Get Created

When you click "Create Jira Issues":

1. Waypoint opens your Jira instance (using the same browser automation)

2. It navigates to the "Create Issue" page

3. It fills in the form fields with data from ServiceNow:
   - **Project**: Uses the project key you configured
   - **Issue Type**: Creates an Epic (for the PRB) and Stories (for incidents)
   - **Summary**: Uses the PRB/incident short description
   - **Description**: Includes the full PRB details
   - **Labels**: Adds labels like "servicenow" and "prb"

4. It submits the form and waits for Jira to create the ticket

5. It captures the new ticket number (like PROJ-123)

6. It repeats this for each related incident (if any)

## Troubleshooting

### "ServiceNow URL not configured"

**Problem**: You haven't set up the ServiceNow URL yet.

**Solution**: Go to Integrations → ServiceNow Integration and enter your ServiceNow URL.

---

### "ServiceNow login required"

**Problem**: You're not logged into ServiceNow, or your session expired.

**Solution**: 
1. Open ServiceNow in your browser
2. Log in normally
3. Try again in Waypoint

---

### "Timeout loading PRB"

**Problem**: ServiceNow took too long to respond, or the PRB number doesn't exist.

**Solution**:
1. Check that the PRB number is correct
2. Make sure you can open the PRB in your browser manually
3. Try again - sometimes ServiceNow is just slow

---

### "Invalid JSON in field mapping"

**Problem**: You tried to customize field mapping but the JSON format is wrong.

**Solution**: 
1. Leave the field mapping blank to use defaults
2. Or check that your JSON is valid (use a JSON validator online)

---

### Can't see the PRB details after clicking Validate

**Problem**: The browser automation might be blocked or ServiceNow's page structure changed.

**Solution**:
1. Check the Logs tab for error messages
2. Make sure ServiceNow loaded properly in the browser
3. The field IDs might have changed - this needs a code update

## Advanced: Custom Field Mapping

If your ServiceNow instance uses different field names, you can customize the mapping:

```json
{
  "prb_number": "problem.number",
  "title": "problem.short_description",
  "description": "problem.description"
}
```

This tells Waypoint which ServiceNow field IDs to look for.

## Privacy & Security

- **No passwords stored**: Waypoint uses your existing browser session
- **No API keys needed**: Works with browser automation, not APIs
- **Local only**: All data stays on your computer
- **You control when**: Nothing happens automatically - you click the buttons

## Summary

**For Non-Technical Users:**
- Think of it as a smart assistant that copies PRB info into Jira for you
- You just need to give it the PRB number
- It does the tedious copying for you

**For Technical Users:**
- Uses Selenium WebDriver to scrape ServiceNow web UI
- Builds direct links to PRBs using `sysparm_query`
- Extracts data by field IDs
- Creates Jira tickets via web form automation
- No REST APIs required on ServiceNow side

---

*Need help? Check the Logs tab for detailed error messages, or submit feedback using the 🐛 button.*
