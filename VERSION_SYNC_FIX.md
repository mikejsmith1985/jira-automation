# v1.2.9 Old UI Issue - Root Cause & Fix

## Problem
v1.2.9 was showing the old UI instead of the new modern-ui.html

## Root Cause
**APP_VERSION constant in app.py was out of sync with the release tag**

### Timeline of Events
1. Merged PR #10 (PR lifecycle tracking + version checker)
2. Bumped APP_VERSION to "1.2.5" in app.py
3. Pushed to main → auto-release workflow created v1.2.7 (good!)
4. Pushed release notes docs → auto-release workflow created v1.2.8 (bad - docs only)
5. Pushed more docs → auto-release workflow created v1.2.9 (bad - docs only)
6. Pushed more docs → auto-release workflow created v1.2.10 (bad - docs only)

### Why Old UI Appeared
- v1.2.9 release was built from app.py with APP_VERSION = "1.2.5"
- The app's version constant didn't match the release tag
- This likely caused the app to display cached old UI or fallback to default

### Why This Happened
The **auto-release-on-main.yml** workflow was triggered on **every** push to main:
- Not just code changes
- Also documentation commits
- This caused version inflation and mismatches

## Solution Implemented

### ✅ Disabled Auto-Release on Push
`yaml
# BEFORE
on:
  push:
    branches:
      - main

# AFTER
on:
  workflow_dispatch:  # Manual only
`

This prevents:
- Accidental releases from documentation commits
- Version number inflation
- Version mismatches between release tag and APP_VERSION

## How to Release Now

### Method 1: Manual Version Bump (RECOMMENDED)
`ash
# 1. Update version in app.py
sed -i 's/APP_VERSION = .*/APP_VERSION = "1.2.11"/' app.py

# 2. Commit and push
git add app.py
git commit -m "chore: Bump version to 1.2.11"
git push origin main

# 3. Manual trigger (if auto-trigger doesn't work)
gh workflow run auto-release-on-main.yml --ref main
`

### Method 2: Manual Trigger
`ash
gh workflow run auto-release-on-main.yml --ref main
`

Then the workflow will:
1. Calculate next version from latest tag
2. Update APP_VERSION in app.py
3. Build executable
4. Create release with assets

## Current Status

| Release | Status | Issue |
|---------|--------|-------|
| v1.2.7  | ✅ GOOD | Working (modern UI) |
| v1.2.8  | ❌ BAD | Old UI (version mismatch) |
| v1.2.9  | ❌ BAD | Old UI (version mismatch) - **THIS ONE** |
| v1.2.10 | ❌ BAD | Version conflict (tag collision) |

**USE v1.2.7** until we release v1.2.11 with the fix

## Prevention
- Auto-release is now disabled
- Only manual triggers (workflow_dispatch) work
- Version bumps must be intentional
- No more accidental releases from docs commits
