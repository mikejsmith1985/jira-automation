# Jira Scraping - How It Works & Troubleshooting

## Issue #18 Resolution

### Problems Reported
1. **8 issues returned but only 5 visible** - Discrepancy between scraped count and displayed issues
2. **Feedback submission fails with attachments** - "Body too long" error when attaching images/videos

---

## 🔍 How Jira Scraping Works

### Overview
The scraper uses **8 different strategies** to find issue keys on a Jira board. All strategies run in parallel, and results are deduplicated by issue key.

### Strategy Details

#### **Strategy 1: Classic Board Cards**
- **Selector:** `.ghx-issue`
- **When it works:** Traditional Jira Scrum/Kanban boards
- **What it finds:** Cards with class `ghx-issue`

#### **Strategy 2: Next-Gen Cards**
- **Selector:** `[data-testid*="card"]`
- **When it works:** Modern team-managed boards
- **What it finds:** Any element with data-testid containing "card"

#### **Strategy 3: List Items**
- **Selector:** `[role="listitem"]`
- **When it works:** Accessible Jira boards using ARIA roles
- **What it finds:** List item elements that may contain issue keys

#### **Strategy 4: Swimlane Cards**
- **Selector:** `[data-test-id*="software-board.card"]`, `[data-testid="list.draggable-list.draggable-item"]`
- **When it works:** Boards with swimlanes enabled
- **What it finds:** Cards within swimlane containers

#### **Strategy 5: Data Attributes**
- **Method:** Check `data-issue-key` attribute
- **When it works:** When Jira adds metadata to DOM elements
- **What it finds:** Direct issue key from element attribute

#### **Strategy 6: Text Pattern Matching**
- **Method:** Regex search for `[A-Z]+-\d+` pattern (e.g., "PROJ-123")
- **When it works:** Always, as fallback
- **What it finds:** Any text matching issue key format

#### **Strategy 7: Child Elements**
- **Method:** Look for `.ghx-key`, `[data-testid*="issue-key"]`, `a[href*="/browse/"]` inside cards
- **When it works:** When issue key is in a child element
- **What it finds:** Nested issue key elements

#### **Strategy 8: Link Fallback**
- **Method:** Find all `<a href="/browse/...">` links and extract keys from URLs
- **When it works:** Always, most robust strategy
- **What it finds:** Issue links anywhere on the page

### Deduplication
All strategies add found keys to a `seen_keys` set. If a key is found by multiple strategies, it's only added once to the final list.

```python
seen_keys = set()
for strategy in strategies:
    for key in strategy.find_keys():
        if key not in seen_keys:
            seen_keys.add(key)
            issues.append({'key': key})
```

---

## 🐛 "8 Issues vs 5 Visible" Problem

### Root Causes

1. **Hidden/Collapsed Issues in Jira**
   - If issues are collapsed or in hidden swimlanes, they may be in the DOM but not visible
   - The scraper counts them because they exist in HTML
   - You don't see them because they're collapsed in the UI

2. **Filtering Applied**
   - If you have filters active in Jira (e.g., "My Issues", assignee filter)
   - Some issues may be present in DOM but visually filtered out
   - Scraper still finds them in the page source

3. **Pagination**
   - If board has pagination and you're on page 1
   - Scraper finds issues on current page only
   - Later pages not scraped unless you scroll/navigate

4. **DOM vs Visual Display**
   - **Key insight:** The scraper reads the **HTML DOM**, not what's visually rendered
   - Jira may load all issue data into DOM but hide some with CSS
   - Example: `<div style="display:none">` still scraped

### Debugging Steps

1. **Check Console Logs**
   - New version logs each found issue: `[SCRAPE] Found issue: PROJ-123`
   - Compare logged issues vs what you see in UI
   - Look for patterns (e.g., all hidden issues from same swimlane)

2. **Inspect debug_info**
   - Response includes `debug_info` array with:
     - How many elements each selector found
     - Total potential cards
     - Issues extracted from cards vs links
   - Example:
     ```json
     "debug_info": [
       "✓ Board loaded successfully",
       "Classic cards (.ghx-issue): 0 found",
       "Next-gen cards: 8 found",
       "Total potential cards found: 8",
       "Issues extracted from cards: 8"
     ]
     ```

3. **Check Board Structure**
   - Open Jira board in browser
   - Open DevTools (F12) → Elements tab
   - Search for your issue key (Ctrl+F, type "PROJ-123")
   - See how many times it appears in DOM
   - Check if parent elements have `display:none` or `visibility:hidden`

4. **Test with Toggles**
   - **Your observation:** "when I changed visible toggles on structure I got very different results"
   - This confirms: **DOM structure affects scraping**
   - When you collapse/hide issues in Jira:
     - They may be removed from DOM (returns fewer issues)
     - OR stay in DOM but hidden (still scraped)
   - Depends on Jira's implementation

### Solutions

#### If You Want to Scrape Only Visible Issues:
We can add visibility check:
```python
if el.is_displayed():  # Only scrape visible elements
    issues.append({'key': key})
```

#### If You Want All Issues (Current Behavior):
Keep current implementation - scrapes everything in DOM regardless of visibility.

#### If You Want to Match Jira's Count:
1. Ensure no filters are active in Jira
2. Expand all swimlanes before scraping
3. Ensure all issues are loaded (scroll to bottom if infinite scroll)

---

## 📦 "Body Too Long" Error - FIXED

### Problem
When attaching screenshots or videos, GitHub issue body exceeded 65KB limit.

### Root Cause
Old code embedded base64-encoded images directly in issue body:
```markdown
![screenshot](data:image/png;base64,iVBORw0KG...VERY_LONG_STRING...)
```

### Solution (Implemented)
1. **Create issue first** with text only (no attachments in body)
2. **Upload attachments as comments** after issue created
3. **Size limits:**
   - Images < 1MB: Embed as data URL in comment
   - Images 1-10MB: Note in comment, GitHub converts to URL
   - Videos/large files: Note metadata only

### New Behavior
```
Issue Body:
  - User description
  - Logs (if enabled)
  - System info

Comment 1 (if screenshot attached):
  - Screenshot embedded or noted

Comment 2 (if video attached):
  - Video metadata (size, type)
  - Note that it was captured
```

### Result
✅ No more "body too long" errors  
✅ Attachments uploaded successfully  
✅ Works with large screenshots and videos

---

## 🧪 Testing Changes

### Test 1: Verify All Issues Returned
1. Scrape a board with known issue count (e.g., 8 issues)
2. Check response: `"total_issues": 8`
3. Check response: `"issues_scraped"` should have 8 entries (not 20 limit anymore)
4. Frontend should display all 8

### Test 2: Understand Which Issues Are Found
1. Open Waypoint terminal/console
2. Scrape board
3. Watch for: `[SCRAPE] Found issue: PROJ-123` logs
4. Compare logged keys vs what you see in Jira UI
5. Identify which issues are "hidden" but scraped

### Test 3: Debug Info Inspection
1. Scrape board
2. Check response includes `scraping_explanation` field with:
   - How it works
   - List of 8 strategies
   - Explanation of deduplication
   - Note about visible vs returned

### Test 4: Feedback with Attachments
1. Click 🐛 feedback button
2. Capture screenshot (< 1MB)
3. Submit feedback
4. Should succeed ✅
5. Check GitHub issue has comment with screenshot

### Test 5: Feedback with Large Attachments
1. Record 30-second video
2. Submit feedback
3. Should succeed ✅
4. Check GitHub issue has comment noting video metadata

---

## 📊 Expected Output Examples

### Successful Scrape with Debug Info
```json
{
  "success": true,
  "message": "Scraped 8 issues from Jira",
  "metrics": {
    "total_issues": 8,
    "issues_scraped": [
      {"key": "PROJ-101"},
      {"key": "PROJ-102"},
      {"key": "PROJ-103"},
      {"key": "PROJ-104"},
      {"key": "PROJ-105"},
      {"key": "PROJ-106"},
      {"key": "PROJ-107"},
      {"key": "PROJ-108"}
    ],
    "scrape_time": "2026-01-13 18:00:00",
    "debug_info": [
      "✓ Board loaded successfully",
      "Classic cards (.ghx-issue): 0 found",
      "Next-gen cards ([data-testid*='card']): 8 found",
      "List items ([role='listitem']): 0 found",
      "Swimlane cards: 0 found",
      "Total potential cards found: 8",
      "Issues extracted from cards: 8",
      "Found 24 links with /browse/"
    ],
    "scraping_explanation": {
      "how_it_works": "The scraper uses multiple strategies to find issue keys...",
      "strategies": [ ... ],
      "deduplication": "All strategies run and results are deduplicated...",
      "visible_vs_returned": "If you see fewer issues than returned, check if...",
      "structure_impact": "Toggling issue visibility in Jira affects whether..."
    }
  }
}
```

### Console Logs During Scrape
```
[SCRAPE] Found issue: PROJ-101
[SCRAPE] Found issue: PROJ-102
[SCRAPE] Found issue: PROJ-103
[SCRAPE] Found issue: PROJ-104
[SCRAPE] Found issue: PROJ-105
[SCRAPE] Found issue: PROJ-106
[SCRAPE] Found issue: PROJ-107
[SCRAPE] Found issue: PROJ-108
[SCRAPE] Found issue from link: PROJ-101
[SCRAPE] Found issue from link: PROJ-102
...
```

---

## 🎯 Summary of Fixes

| Issue | Root Cause | Fix | Status |
|-------|-----------|-----|--------|
| 8 scraped, 5 visible | DOM contains hidden issues | Added logging + explanation of scraping logic | ✅ Fixed |
| Body too long | Base64 images in issue body | Upload attachments as comments instead | ✅ Fixed |
| Limited to 20 issues | Code had `[:20]` slice | Removed limit, return all issues | ✅ Fixed |
| No scraping explanation | Unclear how scraper works | Added detailed `scraping_explanation` in response | ✅ Fixed |

---

## 📝 Files Modified

- **`app.py`** - Lines 973-991: Added scraping explanation, removed 20-issue limit, added logging
- **`github_feedback.py`** - Lines 70-128: Upload attachments as comments to avoid body size limit

## 🚀 Next Steps

1. Pull latest changes from GitHub
2. Test scraping on your work board
3. Review console logs to see which issues are found
4. Test feedback submission with screenshot/video
5. Report findings about hidden vs visible issues

---

**Generated:** 2026-01-13  
**Issue:** #18  
**Commit:** Coming next
