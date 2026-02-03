# Release v1.4.5 - Log Encoding Fix

## Summary
Fixed GitHub issue #39: UTF-8 decode error when capturing logs during PRB validation feedback submission.

## Problem
- User reported "PRB Validation Failed" with error: `'utf-8' codec can't decode byte 0xd7 in position 4894: invalid continuation byte`
- Error occurred when feedback system tried to capture application logs
- Log file contained non-UTF-8 characters (likely from browser console, SNOW data, or extended ASCII)
- Strict UTF-8 encoding caused crash instead of graceful handling

## Solution
Added error handling to all log file read operations:

### Files Modified
1. **github_feedback.py** (line 254)
   - `LogCapture.capture_recent_logs()` method
   - Changed: `open(log_file, 'r', encoding='utf-8')`
   - To: `open(log_file, 'r', encoding='utf-8', errors='replace')`

2. **app.py** (line 2456)
   - `handle_export_logs()` method
   - Changed: `open(log_file, 'r', encoding='utf-8')`
   - To: `open(log_file, 'r', encoding='utf-8', errors='replace')`

### How It Works
The `errors='replace'` parameter tells Python to:
- Replace invalid UTF-8 byte sequences with � (U+FFFD replacement character)
- Continue reading the file instead of crashing
- Allow feedback submission and log export to succeed

### Benefits
- ✅ Feedback system works reliably with any log content
- ✅ No more crashes from special characters in logs
- ✅ Log export always succeeds
- ✅ Graceful degradation (shows � for invalid chars instead of failing)

## Testing
Tested scenarios:
- Log files with extended ASCII characters
- Browser console logs with emojis
- ServiceNow data with special characters
- Mixed encoding log entries

All scenarios now handle gracefully without crashes.

## Commits
- 2d96156: Fix #39: Handle UTF-8 decode errors in log file reading
- ffa947e: Bump version to 1.4.5

## Release
- **Version**: v1.4.5
- **Tag**: v1.4.5
- **Build**: Successful (~2 minutes)
- **Assets**: waypoint.exe, waypoint-portable.zip
- **Release URL**: https://github.com/mikejsmith1985/jira-automation/releases/tag/v1.4.5

## Impact
- **Severity**: High (blocked feedback submission)
- **Users Affected**: Anyone with non-UTF-8 characters in logs
- **Priority**: Critical bug fix

## Follow-up
Consider future enhancement:
- Add encoding detection (chardet library) to auto-detect log encoding
- Support multiple log encodings (UTF-8, Latin-1, Windows-1252)
- Add warning in UI when replacement characters are used

## Status
✅ Issue #39 resolved
✅ v1.4.5 released
✅ GitHub Actions workflow successful
✅ All changes committed and pushed
