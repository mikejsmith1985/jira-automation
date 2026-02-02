# Version 1.2.40 - Release Summary

## Issues Fixed

### 1. Issue #31 - SNOW Handler Methods Missing
**Status**: ✅ FIXED  
**Root Cause**: Methods were accidentally nested inside `open_browser()` function instead of being in `SyncHandler` class  
**Fix**: Moved all SNOW-related methods into the `SyncHandler` class:
- `handle_test_snow_connection()` - line 2465
- `handle_validate_prb()` - line 2485
- `handle_snow_jira_sync()` - line 2509
- `handle_get_snow_config()` - line 2422
- `handle_save_snow_config()` - line 2438

**Verification**: 
```bash
python -c "from app import SyncHandler; print('handle_test_snow_connection' in dir(SyncHandler))"
# Output: True ✅
```

### 2. Config Persistence Issue
**Status**: ✅ FIXED  
**Problem**: Users had to re-enter credentials after each app update  
**Root Cause**: Config stored in executable directory, which changes with each version  
**Fix**: Changed `DATA_DIR` to use persistent location:
- **Executable mode**: `%APPDATA%\Waypoint\` (e.g., `C:\Users\YourName\AppData\Roaming\Waypoint\`)
- **Script mode**: Script directory (unchanged)
- **Auto-migration**: Old config automatically copied to new location on first run

**Files Affected**:
- `config.yaml` - User configuration
- `feedback.db` - Feedback history
- `jira-sync.log` - Application logs

### 3. Screenshot Attachment Error Handling
**Status**: ✅ IMPROVED  
**Problem**: Screenshot uploads failed silently, no error messages shown to user  
**Improvements**:
- Added detailed error logging for failed uploads
- Show upload progress: "Uploading screenshot 1/3..."
- Log success/failure for each screenshot
- Display summary: "3 screenshot(s) attached to issue" or "2 screenshot(s) failed to upload - check token permissions"
- Better error messages with status codes and GitHub error details

**Error Handling Added**:
```javascript
// Before: Silent failure
catch (err) {
    console.warn('Screenshot upload failed:', err);
}

// After: Detailed logging
if (uploadRes.ok) {
    addLog('success', `Screenshot ${i + 1} uploaded successfully`);
} else {
    const errorData = await uploadRes.json();
    const errorMsg = `Screenshot upload failed: ${uploadRes.status} - ${errorData.message}`;
    console.error(errorMsg, errorData);
    addLog('error', errorMsg);
}
```

## Changes Summary

### Code Changes
1. **app.py** - Main application file
   - Fixed SNOW handler methods placement (moved into SyncHandler class)
   - Updated `get_data_dir()` to use `%APPDATA%\Waypoint\`
   - Added config migration logic
   - Added screenshot upload error handling
   - Updated FeedbackDB to use DATA_DIR path
   - Bumped version to 1.2.38

### New Files
- **CONFIG_PERSISTENCE_FIX.md** - Detailed explanation of config persistence fix

## Testing Instructions

### Test Issue #31 Fix
1. Build new executable: `.\build.ps1`
2. Run the app
3. Go to Integrations tab
4. Try "Test Connection" for ServiceNow
5. Should work without "'SyncHandler' object has no attribute" error

### Test Config Persistence
1. Run v1.2.38 for first time
2. Configure Jira URL and GitHub token
3. Close app
4. Run a different version (or same version from different location)
5. Config should be preserved (no re-entry needed)

### Test Screenshot Upload Error Handling
1. Open feedback modal (🐛 button)
2. Capture a screenshot
3. Try to submit
4. Check console logs for detailed error messages if upload fails
5. Verify error messages show token permission issues if applicable

## Build Command
```powershell
.\build.ps1
```

This will create:
- `dist\waypoint.exe` - Standalone executable
- Version will show as 1.2.40

## Migration Notes

### For Users Updating from v1.2.39 or Earlier
**First Run After Update**:
- App will automatically copy old `config.yaml` from exe directory to `%APPDATA%\Waypoint\`
- You'll see: `[MIGRATE] Copied config from old location to C:\Users\YourName\AppData\Roaming\Waypoint\config.yaml`
- Your Jira URL, GitHub token, and all settings will be preserved

**No Action Required** - Migration is automatic!

## Technical Details

### SyncHandler Class Structure
```
SyncHandler (line 100 - 2535)
├── do_GET()
├── do_POST()
├── handle_init()
├── handle_save_config()
├── handle_save_integrations()
├── ...
├── handle_save_snow_config() ✅ (line 2438)
├── handle_test_snow_connection() ✅ (line 2465)
├── handle_validate_prb() ✅ (line 2485)
└── handle_snow_jira_sync() ✅ (line 2509)
```

### Data Directory Structure
```
%APPDATA%\Waypoint\
├── config.yaml          # User configuration (Jira, GitHub, etc.)
├── feedback.db          # Feedback submission history
├── jira-sync.log        # Application logs
└── waypoint.lock        # Process lock file
```

## Known Issues & Limitations

### Screenshot Upload Requirements
For screenshots to successfully attach to GitHub issues, the token must have:
- ✅ `repo` scope (write access)
- ✅ Access to create files in the repo
- ✅ The `feedback-screenshots/` folder will be auto-created on first upload

If uploads fail, users will now see clear error messages explaining why.

## Version History
- **v1.2.39** - Previous version
- **v1.2.40** - Current version (SNOW handlers + config persistence + screenshot error handling)

## Next Steps
1. Build the new version: `.\build.ps1`
2. Test SNOW connection and PRB validation
3. Test screenshot uploads with proper error handling
4. Verify config persists across updates
