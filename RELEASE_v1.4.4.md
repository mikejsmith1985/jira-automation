# Release v1.4.4 - ServiceNow UI Fix

## Summary
Fixed GitHub issue #38: "Cannot set properties of null (setting 'innerHTML')" error when validating PRB.

## Problem
- User reported error when clicking "Validate PRB" button
- Error message: "Failed to validate PRB: Cannot set properties of null (setting 'innerHTML')"
- Root cause: ServiceNow/PRB validation UI was completely missing from the application
- Backend API endpoint `/api/snow-jira/validate-prb` existed but had no frontend UI

## Solution
Added complete ServiceNow integration UI to the Settings tab:

### New UI Components (Settings Tab)
1. **ServiceNow Integration Card**
   - ServiceNow URL input
   - Jira Project Key input
   - Save ServiceNow Config button
   - Test Connection button (auto-launches browser)

2. **PRB Validation Test Section**
   - PRB Number input field
   - Validate PRB button
   - Result display area with styled success/error messages

### JavaScript Functions Added
- `saveSnowConfig()` - Saves ServiceNow URL and Jira project to config.yaml
- `testSnowConnection()` - Tests ServiceNow connection (auto-launches browser if needed)
- `validateTestPRB()` - Validates PRB and displays results with proper error handling
- Updated `loadSettings()` to load ServiceNow config on page load

### Features
- ✅ Auto-launch browser when testing or validating (no manual browser tab needed)
- ✅ Styled result display (green for success, red for error, blue for info)
- ✅ Proper error messages with no JavaScript console errors
- ✅ Displays PRB data: number, description, state, priority, related incidents
- ✅ Comprehensive error handling

## Files Modified
- `app.py` - Added ServiceNow UI card, JavaScript functions, config loading

## Commits
- 9a02fe4: Fix #38: Add ServiceNow/PRB validation UI to Settings tab
- b573821: Bump version to 1.4.4

## Release
- **Version**: v1.4.4
- **Tag**: v1.4.4
- **Build**: Successful (1m 55s)
- **Assets**: waypoint.exe, waypoint-portable.zip
- **Release URL**: https://github.com/mikejsmith1985/jira-automation/releases/tag/v1.4.4

## Testing Instructions
1. Launch waypoint.exe v1.4.4
2. Go to **Settings** tab
3. Scroll to **ServiceNow Integration** section
4. Enter ServiceNow URL (e.g., https://yourcompany.service-now.com)
5. Enter Jira Project Key (e.g., PROJ)
6. Click **Save ServiceNow Config**
7. Enter a PRB number (e.g., PRB0123456)
8. Click **Validate PRB**
9. Browser auto-launches if needed
10. Result displays in styled card below

## Status
✅ Issue #38 resolved
✅ v1.4.4 released
✅ GitHub Actions workflow successful
✅ All changes committed and pushed
