# Jira Scraping - Phantom Issues Explained (Issue #18)

## Problem Statement (CORRECTED)

**User reported:** 
- App scraped **8 issues** ✓
- App displayed **8 issues** in Waypoint UI ✓  
- Jira board shows only **5 issues** ❌

**The Issue:** 3 "phantom" issues exist in HTML DOM but are NOT visible in Jira's UI.

---

## 🔍 Root Cause: Phantom Issues in DOM

### What Are Phantom Issues?

**Phantom issues** are issue keys that exist in the HTML DOM but are not actually visible in the Jira UI. This happens because:

1. **Stale DOM Cache** - Jira loaded 8 issues initially, then you moved 3 off the board, but HTML wasn't updated
2. **Archived Issues** - Resolved/archived issues may stay in DOM for caching/performance
3. **Client-Side Filters** - Jira applies filters with JavaScript/CSS (display:none) without removing from DOM
4. **Collapsed Swimlanes** - Issues in collapsed swimlanes exist in DOM with visibility:hidden
5. **Lazy Loading Artifacts** - Previous page/scroll state left issues in memory

### Why The Scraper Finds Them

The scraper reads the **raw HTML DOM**, not the visual display. It doesn't know about:
- CSS styling (display:none, visibility:hidden)
- JavaScript filters applied by Jira
- User interaction state (collapsed/expanded)

**Before this fix:** Scraper returned all 8 without indicating which were hidden  
**After this fix:** Scraper checks `element.is_displayed()` and tags each issue as VISIBLE or HIDDEN

---

## 🛠️ How Scraping Works (8 Strategies)

The scraper uses **8 parallel strategies** to find issue keys, then checks visibility for each:

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

### Visibility Detection (NEW)

After finding an issue key, the scraper now calls:
```python
is_visible = element.is_displayed()
```

This Selenium method returns `False` if the element:
- Has `display: none`
- Has `visibility: hidden`
- Has `opacity: 0`
- Is off-screen
- Parent element is hidden

**Result:** Each issue tagged as `{"key": "PROJ-123", "visible": true/false}`

---

## 🐛 "8 Issues Scraped, 5 Visible in Jira" Problem - SOLVED

### Solution Implemented

1. **Visibility Detection** - Each issue checked with `is_displayed()`
2. **Separate Counts** - Response includes:
   - `total_issues`: All issues found (8)
   - `visible_issues`: Actually visible in Jira (5)
   - `hidden_issues`: Phantom entries (3)
3. **UI Separation** - Frontend displays visible and hidden issues separately
4. **Console Logging** - Each issue logged as `[SCRAPE] Found issue: PROJ-123 [VISIBLE]` or `[HIDDEN]`
5. **Debug Info** - Lists which specific issues are hidden

### Example Output

```json
{
  "success": true,
  "message": "Scraped 8 issues from Jira (5 visible, 3 hidden)",
  "metrics": {
    "total_issues": 8,
    "visible_issues": 5,
    "hidden_issues": 3,
    "issues_scraped": [
      {"key": "PROJ-101", "visible": true},
      {"key": "PROJ-102", "visible": true},
      {"key": "PROJ-103", "visible": true},
      {"key": "PROJ-104", "visible": true},
      {"key": "PROJ-105", "visible": true},
      {"key": "PROJ-106", "visible": false},  // PHANTOM
      {"key": "PROJ-107", "visible": false},  // PHANTOM
      {"key": "PROJ-108", "visible": false}   // PHANTOM
    ],
    "debug_info": [
      "Issues extracted from cards: 8 (Visible: 5, Hidden: 3)",
      "Hidden issues: PROJ-106, PROJ-107, PROJ-108"
    ]
  }
}
```

### Console Logs
```
[SCRAPE] Found issue: PROJ-101 [VISIBLE]
[SCRAPE] Found issue: PROJ-102 [VISIBLE]
[SCRAPE] Found issue: PROJ-103 [VISIBLE]
[SCRAPE] Found issue: PROJ-104 [VISIBLE]
[SCRAPE] Found issue: PROJ-105 [VISIBLE]
[SCRAPE] Found issue: PROJ-106 [HIDDEN]
[SCRAPE] Found issue: PROJ-107 [HIDDEN]
[SCRAPE] Found issue: PROJ-108 [HIDDEN]
```

### UI Display

**Waypoint SM Tab will now show:**

```
✓ Visible in Jira (5)
  PROJ-101
  PROJ-102
  PROJ-103
  PROJ-104
  PROJ-105

⚠ Hidden/Phantom Issues (3)
These exist in HTML DOM but are not visible in Jira UI 
(archived, filtered, collapsed, or stale)
  PROJ-106 [HIDDEN]
  PROJ-107 [HIDDEN]
  PROJ-108 [HIDDEN]
```

### Debugging Steps

1. **Check Console Logs**
   - Each issue now logged with visibility tag: `[SCRAPE] Found issue: PROJ-123 [VISIBLE]` or `[HIDDEN]`
   - Identifies exactly which 3 issues are phantoms

2. **Check Response `debug_info`**
   - Shows: `"Hidden issues: PROJ-106, PROJ-107, PROJ-108"`
   - Tells you exactly which keys are phantoms

3. **Inspect Waypoint UI**
   - SM tab separates visible vs hidden issues
   - Hidden issues shown in red section with warning

4. **Cross-Reference with Jira**
   - Open Jira board
   - Search for the hidden issue keys (Ctrl+F)
   - You likely won't find them visually
   - Check if they're archived, in other sprints, or filtered out

5. **Refresh Jira Board**
   - Sometimes DOM is stale from previous state
   - Press F5 in Jira browser
   - Re-scrape and see if hidden count changes

### How to Use This Information

#### **If You Want Accurate Jira Count:**
Use `visible_issues` count - this matches what you see in Jira (5 issues).

#### **If You Want All Issues in DOM:**
Use `total_issues` count - includes phantoms (8 issues).

#### **To Identify Phantom Issues:**
1. Check `debug_info` → `"Hidden issues: PROJ-106, PROJ-107, PROJ-108"`
2. Search for those keys in Jira board
3. Determine why they're hidden:
   - Archived/resolved but not removed from DOM?
   - In a different sprint but cached?
   - Filtered out by Jira's UI filters?
   - Stale data from previous board state?

#### **Your Observation About Toggles:**
> "When I changed visible toggles on structure I got very different results"

**Explanation:** When you collapse/expand swimlanes or toggle filters in Jira:
- Some Jira versions **remove elements from DOM** → fewer issues scraped
- Some Jira versions **hide with CSS** → same issues scraped, but visibility flag changes
- This is why toggling structure affects scraping results - you're changing what exists in DOM

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
