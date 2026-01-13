# 🚀 Waypoint v1.2.13 - Enhanced Scraping & Auto-Update

## 📦 What's New

### 🔄 Auto-Update Feature
- **Replaced** non-functional "Account Management" with auto-update system
- **Check for updates** with one click in sidebar
- **Automatic download** and installation of new releases
- **Auto-restart** after update completes
- Inspired by Minecraft Forge's update checker
- No login required - uses GitHub public API

**How it works:**
1. Click "Check Updates" in sidebar (bottom-left)
2. App queries GitHub releases
3. Shows dialog with version info, size, release notes
4. Confirm to download and apply
5. App restarts with new version

### 🔍 Enhanced Jira Scraping

#### Phantom Issue Detection
- **Identifies hidden issues** - Issues in DOM but not visible in Jira UI
- **Separate counts** - Shows visible vs hidden issues
- **Visual indicators** - Green section (visible) + Red section (hidden)
- **Explains why** - Archived, filtered, collapsed, or stale DOM

#### Full Issue Data Extraction
- **Before:** Only issue key (PROJ-123)
- **After:** 8 fields per issue
  - 🔑 Key
  - 📝 Summary/Title
  - 📊 Status (In Progress, Done, etc)
  - 👤 Assignee
  - ⚡ Priority (High, Medium, Low)
  - 🏷️ Type (Story, Bug, Task, Epic)
  - 🔗 URL
  - 👁️ Visible flag

**Rich card display:**
```
PROJ-123
Add auto-update feature
📊 In Progress | 👤 John Doe | 🏷️ Story | ⚡ High
https://jira.company.com/browse/PROJ-123
```

### 🐛 Feedback System Improvements

#### Attachment Support Fixed
- **Fixed:** "Body too long" error with screenshots/videos
- **Solution:** Upload attachments as comments (not in body)
- **Size handling:**
  - Images <1MB: Embedded in comment
  - Images 1-10MB: Noted with metadata
  - Videos: Metadata only (type, size)

#### Enhanced Error Handling
- **Alert dialogs** - Impossible to miss errors now
- **Success confirmation** - Shows issue number and URL
- **Detailed logging** - Every step logged to console
- **Actionable errors:**
  - "Bad credentials" → Check token in Settings
  - "Not Found" → Check repository format (owner/repo)
  - "Permission denied" → Token needs repo/public_repo scope
  - "Rate limit" → Try again later

## 🛠️ Technical Details

### Version Comparison
- Uses semantic versioning (packaging library)
- Prevents accidental downgrades
- Cached for 1 hour to avoid rate limits

### Safe Update Process
1. Downloads to temp directory
2. Creates batch script to replace .exe
3. Validates copy success
4. Restarts app only if successful
5. Self-cleaning (batch deletes itself)

### Scraping Strategy
Each field tries multiple selectors:
1. Classic Jira (`.ghx-summary`, `.ghx-end`)
2. Next-gen (`[data-testid*="summary"]`)
3. Generic (`.issue-status`, `.assignee`)
4. Text parsing fallback
5. Graceful degradation (null if not found)

## 📊 Issue Resolution

### Issue #18 - Scraping Discrepancy
**Problem:** App scraped 8 issues but Jira only showed 5  
**Root Cause:** 3 phantom issues in DOM but hidden in UI  
**Solution:** Added visibility detection with `is_displayed()` 

### Feedback Submission Failures
**Problem:** Silent failures, users couldn't see errors  
**Solution:** Added prominent alerts and detailed console logging

## 🔧 API Endpoints

### New Endpoints
- `POST /api/updates/check` - Check for latest release
- `POST /api/updates/apply` - Download and install update

### Enhanced Endpoints
- `POST /api/feedback/submit` - Now handles large attachments via comments

## 📝 Files Changed
- `app.py` - Version bump, update endpoints, enhanced scraping
- `version_checker.py` - Added download_and_apply_update()
- `modern-ui.html` - Replaced Account with Check Updates button
- `assets/js/modern-ui-v2.js` - Update checking UI, rich issue display
- `github_feedback.py` - Attachment upload as comments

## 🎯 Commits in This Release
- bbdb22b - Bump version to 1.2.13
- 293237a - Enhanced scraping to extract full issue data
- 8aedcc8 - Replace Account Management with Auto-Update
- 3a0874e - Add auto-update feature documentation
- 5e21aaf - Fix #18: Detect and separate phantom issues
- 76394ae - Fix #18: Explain scraping logic and fix attachment body size
- c1aeb30 - Add comprehensive error handling for feedback
- cc8970e - Fix Jira scraping and add feedback token configuration

## 📚 Documentation
- `AUTO_UPDATE_GUIDE.md` - Complete auto-update feature guide
- `ISSUE_18_SCRAPING_ANALYSIS.md` - Phantom issues explanation
- `FEEDBACK_ERROR_HANDLING.html` - Error handling dashboard

## ⚠️ Known Limitations
- No signature verification (Windows may show warning)
- Rollback not supported (yet)
- Some fields may be null if not visible on board cards

## 🔮 Future Enhancements
- Auto-check on startup
- Background update checks
- Update notifications in UI
- Rollback to previous version
- Beta/pre-release opt-in

## 💾 Installation

### New Install
1. Download `waypoint.exe`
2. Run the executable
3. Windows may show SmartScreen warning (click "More info" → "Run anyway")

### Update from Previous Version
**Manual:**
1. Download `waypoint.exe`
2. Replace your existing waypoint.exe
3. Restart the app

**Automatic (if on v1.2.10+):**
1. Click "Check Updates" in sidebar
2. Confirm when dialog appears
3. App downloads and restarts automatically

## 🙏 Thanks
Special thanks to the user for:
- Detailed bug reports with clear reproduction steps
- Testing phantom issue detection
- Requesting auto-update feature
- Following @copilot-instructions for clean communication

---

**Release Date:** January 13, 2026  
**Build Size:** 26.12 MB  
**Commits:** 8  
**Issues Resolved:** #18  
**Breaking Changes:** None
