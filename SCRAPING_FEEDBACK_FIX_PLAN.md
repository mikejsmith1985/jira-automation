# Jira Scraping & Feedback Token Issues - Resolution Plan

## Issues Identified

### Issue 1: Jira Board Scraping Returns 0 Issues (Work Account)
**Symptoms:**
- Personal Jira: ✅ Scrapes 2 issues successfully
- Work Jira: ❌ Scrapes 0 issues from 65-issue board
- Selenium successfully opens browser and detects login ✅

**Root Cause Analysis:**
The scraping logic in `app.py` (lines 808-887) uses multiple strategies:
1. Classic Kanban/Scrum selectors (`.ghx-issue`)
2. Next-gen boards (`[data-testid*="card"]`)
3. Generic accessible elements (`[role="listitem"]`)
4. Data attributes (`data-issue-key`)
5. Text pattern matching (`[A-Z]+-\d+`)
6. Fallback link strategy (`a[href*="/browse/"]`)

**Likely Cause:**
Work Jira board uses a different HTML structure not covered by existing selectors. The debug feature (line 885-887) saves `debug_jira_scrape.html` when 0 issues found.

**Solution:**
1. Add debug output to understand work board HTML structure
2. Add more selector strategies
3. Improve error reporting
4. Add board type detection

### Issue 2: Cannot Configure Feedback GitHub Token
**Symptoms:**
- User cannot submit feedback/bugs
- No UI element to configure GitHub Personal Access Token
- Token hardcoded as placeholder: `YOUR_GITHUB_TOKEN_HERE`

**Root Cause:**
The feedback modal (lines 534-587 in modern-ui.html) has no input field for GitHub token. Only the Settings tab has a GitHub token field (line 483) but it's for GitHub API integration, not feedback.

**Solution:**
1. Add feedback token configuration to Settings tab
2. Add API endpoint to save feedback config
3. Show clear instructions when token not configured
4. Test feedback submission workflow

## Implementation Plan

### Fix 1: Enhanced Jira Scraping with Debug Output
- Add console logging for each scraping strategy
- Save HTML when scraping fails
- Add board type detection
- Add manual selector input option for custom boards

### Fix 2: Feedback Token Configuration UI
- Add feedback token input to Settings
- Add validation and save functionality
- Show setup modal when feedback button clicked without token
- Test end-to-end feedback flow

## Files to Modify
- `app.py` - Enhanced scraping logic + feedback config endpoint
- `modern-ui.html` - Add feedback token UI in Settings
- `assets/js/modern-ui-v2.js` - Handle feedback token saving

## Testing Checklist
- [ ] Test scraping on personal Jira (should still work)
- [ ] Test scraping on work Jira with debug output
- [ ] Inspect `debug_jira_scrape.html` to identify selectors
- [ ] Add missing selectors
- [ ] Test feedback token configuration
- [ ] Test feedback submission with configured token
- [ ] Verify GitHub issue gets created
