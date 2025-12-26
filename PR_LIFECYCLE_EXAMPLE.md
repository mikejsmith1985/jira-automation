# Example: How PR Lifecycle Updates Now Work

## Scenario: PR for ticket ABC-123

### 10:00 AM - PR Opened
**Scraped data:**
- status: 'open'
- title: 'ABC-123: Fix login bug'

**Action:**
✅ Comment on ABC-123: '🔗 Pull Request opened: github.com/org/repo/pull/456'
✅ Set status: 'In Review'
✅ Add label: 'has-pr'
📝 State stored: {'repo-456': 'open'}

---

### 11:00 AM - PR Still Open (dev added more commits)
**Scraped data:**
- status: 'open' (same as before)

**Action:**
⏭️ SKIPPED - No state change

---

### 12:00 PM - PR Merged to DEV
**Scraped data:**
- status: 'merged'
- target_branch: 'DEV'

**Action:**
✅ Comment on ABC-123: '✅ Merged to DEV: github.com/org/repo/pull/456 🧪 Ready for Testing'
✅ Set status: 'Ready for Testing'
✅ Add label: 'merged-dev'
📝 State updated: {'repo-456': 'merged'}

---

### 1:00 PM - PR Still Merged
**Scraped data:**
- status: 'merged' (same as before)

**Action:**
⏭️ SKIPPED - No state change

---

## What You Get:
✅ 2 Jira comments per PR (open + merged)
✅ Branch-specific messages based on target (DEV/INT/PVS)
✅ Status transitions match your workflow
✅ No duplicate spam (only comments on state changes)
