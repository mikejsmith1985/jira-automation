# Ready to Test - Version 1.1.0

## 🎯 What's New in v1.1.0

This version adds:
- **Persona System**: Choose PO, Dev, or SM role
- **Dependency Canvas**: Visualize issue dependencies
- **Insights Engine**: Rule-based pattern detection
- **Team Health**: Automated hygiene checks
- **Exports**: CSV for features and reports

## 🚀 Quick Start Testing

### 1. Run the Application

```bash
# Option A: Run from source
python app.py

# Option B: Run packaged executable
.\dist\GitHubJiraSync.exe
```

Browser opens to `http://localhost:5000`

### 2. Select Your Persona

On the dashboard, click one of the three persona cards:
- **👔 PO (Product Owner)**: For feature tracking
- **💻 Dev (Developer)**: For GitHub automation
- **📈 SM (Scrum Master)**: For insights and metrics

Your selection is saved and persists across sessions.

## 🧪 Test Scenarios

### Test 1: Product Owner Features

#### A. Feature Tracking
1. Click **👔 PO** tab
2. Scroll to "Features & Epics" section
3. **Verify**: See sample features with progress bars
4. Click expand button (▼) on any feature
5. **Verify**: Child issues appear with status badges
6. Click **📥 Export CSV** button
7. **Verify**: CSV file downloads with features data

#### B. Dependency Canvas
1. Scroll to "Dependency Canvas" section
2. Click **📖 Show JSON Schema Example**
3. **Verify**: JSON schema and format shown
4. Create a test JSON file (`test-dependencies.json`):
```json
{
  "TEST-100": {
    "key": "TEST-100",
    "summary": "User Login Feature",
    "status": "inprogress",
    "links": [
      { "type": "blocks", "target": "TEST-101" },
      { "type": "depends", "target": "TEST-200" }
    ]
  },
  "TEST-101": {
    "key": "TEST-101",
    "summary": "OAuth Integration",
    "status": "blocked",
    "links": [
      { "type": "blocked-by", "target": "TEST-100" }
    ]
  },
  "TEST-200": {
    "key": "TEST-200",
    "summary": "Database Setup",
    "status": "done",
    "links": []
  }
}
```
5. Click **📁 Upload File** and select your JSON
6. **Verify**: Success message shows "Loaded 3 issues"
7. Type `TEST-100` in the issue key input
8. Click **📊 Load Issue**
9. **Verify**: 
   - Canvas shows 3 cards (TEST-100, TEST-101, TEST-200)
   - Red dashed line from TEST-100 to TEST-101 (blocks)
   - Green solid line with "1" from TEST-200 to TEST-100 (depends)
10. **Try**: Drag cards around - they should move
11. Click a card - it gets a blue border (selected)

#### C. Scrum/Kanban Toggle
1. At top of PO tab, see "Team Mode" section
2. Toggle between 🏃 Scrum and 🌊 Kanban radio buttons
3. **Verify**: Metrics section changes accordingly

### Test 2: Developer Features

1. Click **💻 Dev** tab
2. **Verify**: Automation rules shown with toggle switches
3. Toggle automation rules on/off
4. Click **🔄 Sync All PRs**
5. **Verify**: Status message shows "Syncing..."
6. Click **📋 View Sync Log**
7. **Verify**: Switches to Logs tab

### Test 3: Scrum Master Features

#### A. Insights Engine
1. Click **📈 SM** tab
2. **Verify**: "Team Health Overview" shows stats
3. Scroll to "🤖 Insights" section
4. **Initial state**: Shows "No Insights Yet" placeholder

#### B. Run Hygiene Check
1. Click **🔍 Run Check** button
2. **Verify**: Status shows "Running hygiene check..."
3. Wait 2 seconds
4. **Verify**: Insights section updates with generated insights
5. Each insight should have:
   - Title with emoji
   - Description
   - Timestamp
   - **View** and **✓ Resolve** buttons

#### C. Resolve Insights
1. Click **✓ Resolve** on any insight
2. **Verify**: Success message appears
3. **Verify**: Insight disappears from list (filtered out)

#### D. Export Hygiene Report
1. Scroll to "Hygiene Report" section
2. Click **📥 Export Report**
3. **Verify**: CSV file downloads with format:
```
Issue Type,Count,Severity,Description
Stale Tickets,7,Medium,No updates in 14+ days
...
```

### Test 4: Insights API (Advanced)

#### Test with Sample Data via Console
1. Open browser console (F12)
2. Run this JavaScript:
```javascript
fetch('/api/insights/run', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    jira_data: {
      stories: [
        {
          key: 'TEST-1',
          initial_story_points: 5,
          story_points: 8,
          status: 'In Progress'
        }
      ],
      bugs: [
        {key: 'BUG-1', environment: 'production'},
        {key: 'BUG-2', environment: 'qa'}
      ],
      velocity_history: [40, 42, 45, 38, 35],
      tickets: [
        {
          key: 'TEST-2',
          type: 'Story',
          status: 'In Progress',
          updated: '2024-12-01T00:00:00Z',
          status_changed: '2024-12-01T00:00:00Z'
        }
      ]
    }
  })
}).then(r => r.json()).then(console.log)
```

3. **Expected Response**: JSON with insights array
4. Go back to SM tab and refresh
5. **Verify**: New insights appear

### Test 5: Database Persistence

1. Run hygiene check (generates insights)
2. Close the application completely
3. Restart the application
4. Go to SM tab
5. **Verify**: Previous insights still shown
6. Check `data/insights.db` file exists

### Test 6: Persona Persistence

1. Select a persona on dashboard (e.g., PO)
2. Refresh browser (F5)
3. **Verify**: PO persona still selected
4. Close browser and reopen `http://localhost:5000`
5. **Verify**: PO persona still selected

### Test 7: Settings & Configuration

1. Click **🔧 Settings** tab
2. Enter Jira URL: `https://yourcompany.atlassian.net`
3. Enter GitHub org: `your-org`
4. Enter repos: `repo1, repo2`
5. Click **💾 Save Settings**
6. **Verify**: Success message appears
7. Close and restart app
8. Go back to Settings
9. **Verify**: Settings persisted

### Test 8: Navigation Flow

1. Start on Dashboard
2. Select Dev persona
3. Click each tab: PO → Dev → SM → Workflows → Favorites → Logs → Settings
4. **Verify**: All tabs load without errors
5. **Verify**: Quick actions on dashboard update for persona

## 🐛 What to Look For

### Known Issues (Expected)
- ✅ Canvas PNG export shows "coming soon" message (not implemented yet)
- ✅ Some actions show placeholder messages (backend integration pending)
- ✅ Sample data used until real Jira scraper connected

### Potential Bugs to Report
- ❌ JavaScript errors in browser console
- ❌ Insights not persisting after restart
- ❌ Canvas cards not draggable
- ❌ CSV export fails
- ❌ Persona selection not saving
- ❌ Database errors in Python console
- ❌ UI elements not responsive on small screens

## 📊 Success Criteria

### Must Pass
- [x] All three personas selectable and functional
- [x] Dependency canvas loads from JSON file
- [x] Insights engine generates alerts from sample data
- [x] Exports produce valid CSV files
- [x] Database persists insights across restarts
- [x] Persona selection persists in localStorage

### Nice to Have
- [ ] No console errors
- [ ] Smooth animations
- [ ] Fast load times (<2s)
- [ ] All buttons have hover effects

## 🔍 Database Inspection

To inspect the insights database:

```bash
# Open database (sqlite3 comes with Python on Windows)
sqlite3 data/insights.db

# View insights
SELECT * FROM insights;

# View metrics history
SELECT * FROM metrics_history;

# Exit
.quit
```

## 📝 Test Report Template

```markdown
## Test Report - v1.1.0

**Tester:** [Your Name]
**Date:** [Date]
**Environment:** Windows/Mac/Linux

### Persona Tests
- [ ] PO: Feature tracking
- [ ] PO: Dependency canvas
- [ ] PO: CSV export
- [ ] Dev: Automation rules UI
- [ ] Dev: Sync controls
- [ ] SM: Insights engine
- [ ] SM: Hygiene report

### Technical Tests
- [ ] Database persistence
- [ ] Persona localStorage
- [ ] API endpoints
- [ ] Settings save/load

### Issues Found
1. [Describe issue]
2. [Describe issue]

### Overall Assessment
[Pass/Fail] - [Brief summary]
```

## 🎓 Tips for Testing

1. **Check browser console** (F12) for JavaScript errors
2. **Check Python console** for backend errors
3. **Test with real Jira data** structure if available
4. **Try edge cases**: empty data, large datasets, invalid JSON
5. **Test on different screen sizes** (resize browser)
6. **Test navigation** between all tabs multiple times

## 🚧 Not Yet Implemented (Don't Test)

- Canvas PNG export (button shows "coming soon")
- Real GitHub PR sync (uses placeholder)
- Real Jira data scraping (uses samples)
- Scheduler start/stop (placeholder)
- Workflow individual execution (placeholder)
- Config YAML editor (manual edit only)

## ✅ Ready to Ship When...

- All "Must Pass" criteria met
- No critical bugs in console
- Database persistence working
- Exports producing valid files
- Persona system functional

---

**Questions?** Check the main README.md or DEVELOPMENT_STATUS.md for more details.
