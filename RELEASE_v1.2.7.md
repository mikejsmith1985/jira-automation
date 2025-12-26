## ✅ Release v1.2.7 Complete!

### 🎯 What Was Released:

**Commit:** 17400d3 - chore: Bump version to 1.2.5 
**Tag:** v1.2.7 (auto-bumped by workflow)
**Status:** ✅ Published with assets

### 📦 Assets Included:

- **JiraAutomationAssistant.exe** (24.38 MiB) - Standalone executable
- **GitHubJiraSync.exe** (24.38 MiB) - Alternative name for same binary  
- **Jira-Automation-Assistant-Portable.zip** (24.12 MiB) - Portable version with all dependencies

### ✨ Features in This Release:

#### 1. PR Lifecycle State Tracking
- Fixed duplicate prevention to enable state-based updates
- Detects PR transitions: open → merged/closed
- Multiple Jira comments per PR (one per state change)
- Branch-specific rules for DEV/INT/PVS/REL/PRD
- Logs state changes for visibility

#### 2. Version Update Checker
- New \ersion_checker.py\ module (like forge-terminal)
- Checks GitHub API for latest release
- Semantic version comparison using packaging library
- 1-hour caching to avoid rate limits
- API endpoints:
  - GET /api/version - Current version
  - GET /api/version/check - Check for updates
  - GET /api/version/releases - List releases

#### 3. Release Workflow Improvements
- Added build-and-attach job to auto-release-on-main.yml
- Now generates Windows .exe files automatically on release
- Supports manual reruns with workflow_dispatch trigger
- Fixed v1.2.4 release with missing assets

#### 4. Hourly Sync Schedule
- Business hours only (9am-6pm weekdays)
- 24-hour lookback window
- Perfect for dev workflow: branch → PR → merge → Jira status

### 🔄 Release Workflow Timeline:

| Time | Action | Status |
|------|--------|--------|
| Push to main | Trigger auto-release | ✅ |
| auto-release job | Create tag v1.2.7 | ✅ 7s |
| build-and-attach job | Build exe and assets | ✅ 1m41s |
| Release published | All assets attached | ✅ |

### 🚀 Download

**GitHub Release:** https://github.com/mikejsmith1985/jira-automation/releases/tag/v1.2.7

### 📝 Release Notes

Supports hourly PR sync with:
- State-aware Jira updates
- Branch-specific automation rules
- Version update detection
- Complete extension architecture

