# 🏷️ fixVersion Creator - Quick Reference

## Access
**Waypoint App → SM Tab → "Create fixVersions" card**

## Input Fields
| Field | Description | Example |
|-------|-------------|---------|
| **Project Key** | Jira project identifier | `KAN` |
| **Release Dates** | One date per line | `2026-02-05`<br>`2026-02-12` |
| **Format** | Version name template | `Sprint {month_short} {day}` |
| **Description** | Optional description | `Sprint ending on {date}` |

## Format Options
| Template | Output |
|----------|--------|
| `Sprint {month_short} {day}` | Sprint Feb 05 |
| `v{year}.{month}.{day}` | v2026.02.05 |
| `Release {date}` | Release 2026-02-05 |
| `{month_name} {day} Sprint` | February 05 Sprint |
| `v{year}.{month}` | v2026.02 |

## Placeholders
- `{date}` → 2026-02-05
- `{year}` → 2026
- `{month}` → 02
- `{day}` → 05
- `{month_name}` → February
- `{month_short}` → Feb

## Buttons
- **Preview Names** → See what versions will be created (no changes)
- **Create Versions** → Actually create versions in Jira

## Results
Shows summary with:
- ✅ **Created**: Successfully created versions
- ⏭️ **Skipped**: Already existed (safe to run multiple times)
- ❌ **Failed**: Errors with details
- 🔗 **Link**: Opens Jira versions page

## Prerequisites
1. Jira browser must be open
2. Must be logged into Jira
3. Must have project admin permissions

## Example Workflows

### Bi-Weekly Sprints
```
Project: SCRUM
Dates:
2026-02-05
2026-02-19
2026-03-05
2026-03-19

Format: Sprint {month_short} {day}
```

### Monthly Releases
```
Project: PROD
Dates:
2026-03-01
2026-04-01
2026-05-01

Format: v{year}.{month}
```

### Custom Names
```
Project: KAN
Dates:
2026-02-28

Format: Release {month_name} {year}
Description: End of {month_name} release
```

## Tips
✅ Use YYYY-MM-DD format (with leading zeros)  
✅ Preview first to check names  
✅ Safe to run multiple times (skips duplicates)  
✅ Browser stays on versions page after creation  
✅ Can create up to 50+ versions at once

## Common Issues
**"Browser not open"** → Open Jira browser in Integrations tab first  
**"Not logged in"** → Login to Jira in the browser window  
**"Invalid date"** → Use YYYY-MM-DD format (e.g., 2026-02-05)  
**"Permission denied"** → Need project admin role in Jira

## See Also
- Full guide: `FIXVERSION_WAYPOINT_INTEGRATION.md`
- API docs: `FIXVERSION_CREATOR_README.md`
- CLI usage: `FIXVERSION_QUICKSTART.md`
