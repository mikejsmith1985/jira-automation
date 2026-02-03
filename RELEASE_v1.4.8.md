# Release v1.4.8 - Update Process Diagnostics

**Release Date**: 2025-01-22  
**Type**: Bug Fix Release  
**Focus**: Update mechanism visibility and debugging

## 🐛 Bug Fixes

### Update Process Visibility (#40 investigation)
**Issue**: Update process failing silently - users couldn't see what was wrong
**Root cause**: Batch script running with CREATE_NO_WINDOW flag hid all errors
**Fix**:
- **Show update console window** - User can now see update progress in real-time
- **Detailed logging** - Creates `%TEMP%\waypoint_update.log` with full diagnostics
- **Better error handling** - Exit codes and error messages logged
- **Increased wait time** - 2→3 seconds for app to close before update
- **Verbose output** - Shows source/target paths, timestamps, copy results

**Files Changed**:
- `version_checker.py`: Enhanced update batch script with logging and visibility

### What You'll See Now

When updating:
1. **Download completes** - Message shows log file location
2. **Console window appears** - Shows "Waiting for Waypoint to close..."
3. **Update progress visible** - "Applying update...", "Update complete!"
4. **Log file created** - Check `%TEMP%\waypoint_update.log` if issues occur

### Troubleshooting

If update still fails:
1. Check the console window messages
2. Review `%TEMP%\waypoint_update.log` for error codes
3. Ensure you're not running from temp directory (v1.4.6 blocks this)
4. Verify permissions on the waypoint.exe location
5. Try running as Administrator if on locked-down system

## 📋 How to Update

**From v1.4.7 or earlier**:
1. Settings → Check for Updates
2. Click "Apply Update" if available
3. **Watch the console window** that appears
4. App restarts automatically on success
5. If it fails, check the log file shown in the message

**Manual Update** (if auto-update fails):
1. Download `waypoint.exe` from GitHub releases
2. Close the old app completely
3. Replace the old exe with new one
4. Run the new exe

## 🔍 Technical Details

**Update Script Changes**:
```batch
# Before (v1.4.7)
- Hidden window (CREATE_NO_WINDOW)
- No logging
- 2 second wait
- Minimal error handling

# After (v1.4.8)
+ Visible console window
+ Full diagnostic logging to waypoint_update.log
+ 3 second wait for clean shutdown
+ Detailed error codes and troubleshooting info
```

**Log Output Format**:
```
[2025-01-22 HH:MM:SS] Update started
Source: C:\Users\...\Temp\waypoint_update.exe
Target: C:\...\waypoint.exe
Waiting 3 seconds...
Copying new executable...
Copy exit code: 0
Update successful!
Application restarted
[2025-01-22 HH:MM:SS] Update complete
```

## 🧪 Testing

**Tested scenarios**:
- ✅ Update from permanent location (Desktop, Documents)
- ✅ Update blocked from temp directory (v1.4.6 protection)
- ✅ Console window visibility
- ✅ Log file creation and contents
- ✅ Error code capture on failure
- ✅ Automatic restart after success

**User testing requested**:
- Update from v1.4.5 → v1.4.8 (test diagnostics on old version)
- Report any error codes or log contents if update fails

## 📦 Release Assets

- `waypoint.exe` - Windows executable (51MB)
- Built with PyInstaller + Playwright
- No installation required, run directly

## 🔗 Related Issues

- Fixes visibility issues reported in update process investigation
- Helps diagnose the intermittent update failures users experienced
- Completes the update reliability fixes started in v1.4.6

## ⚠️ Known Limitations

- Console window stays open until update completes (intentional for debugging)
- Log file location is system temp directory (check message for exact path)
- If update batch script is blocked by antivirus, log file won't be created

## 🚀 Next Steps

With visible diagnostics, users can now:
1. See exactly where update fails
2. Report specific error codes
3. Troubleshoot permissions/antivirus issues
4. Verify update script execution

If you see errors, please report:
- Error code from console or log
- Source/target paths from log
- Your OS and permission setup
- Whether running as Admin or standard user

---

**Full Changelog**: https://github.com/mikejsmith1985/jira-automation/compare/v1.4.7...v1.4.8
