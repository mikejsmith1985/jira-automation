# Release v1.4.6 - Update Process Fix

## Summary
Fixed issue where application updates fail to persist when running from temporary directory.

## Problem Reported by User
"The update process still is failing. Is it because I need to save the file instead of just opening it? When I just open it, it runs from a temp file."

## Root Cause
When users download `waypoint.exe` and click **"Open"** instead of **"Save"**:

1. Windows extracts the file to a temporary directory:
   - `C:\Users\{user}\AppData\Local\Temp\MicrosoftEdgeDownloads\{random}\waypoint.exe`
   - Or similar temp location

2. Application detects `sys.executable` pointing to temp folder

3. Update downloads new version successfully

4. Update script runs: `copy /Y "{new_exe}" "{temp_exe}"`
   - Replaces the temp file
   - Update appears to succeed

5. User restarts app from temp location
   - Still sees old version
   - Or temp folder is cleaned, app is gone

**Result**: Updates never persist because they're replacing a temporary copy.

## Solution

### Changes in v1.4.6

#### 1. Detection (version_checker.py)
Added `_is_running_from_temp()` method that checks if executable path contains:
- System temp directory (`tempfile.gettempdir()`)
- User's AppData\Local\Temp
- Any path segment containing `\temp\` or `temp\`

```python
def _is_running_from_temp(self):
    """Check if executable is running from a temporary directory"""
    temp_paths = [
        tempfile.gettempdir().lower(),
        os.path.join(os.path.expanduser('~'), 'appdata', 'local', 'temp').lower(),
        'temp\\',
        '\\temp\\'
    ]
    exe_path_lower = self.current_exe.lower()
    return any(temp_path in exe_path_lower for temp_path in temp_paths)
```

#### 2. Update Blocking (version_checker.py)
`download_and_apply_update()` now checks for temp execution and returns error:

```python
if self.running_from_temp:
    return {
        'success': False,
        'error': 'Cannot update: Application is running from a temporary directory. Please SAVE the executable to a permanent location (e.g., Desktop or Program Files) and run it from there. Then try updating again.'
    }
```

#### 3. UI Warning (app.py)
Update check response includes warning:

```python
if checker.running_from_temp:
    result['warning'] = '⚠️ Running from temporary directory. Updates will not persist. Please SAVE the executable to a permanent location (Desktop, Program Files, etc.) before updating.'
```

### User Experience

**Before v1.4.6:**
1. User clicks "Open" on downloaded exe
2. Update appears to succeed
3. Restart shows old version (confusing!)

**After v1.4.6:**
1. User clicks "Open" on downloaded exe
2. Update button shows warning: "⚠️ Running from temporary directory..."
3. If user tries to update anyway: Clear error message with instructions
4. User must save to permanent location first

## Recommended Locations for EXE

✅ **Good locations:**
- Desktop: `C:\Users\{user}\Desktop\`
- Documents: `C:\Users\{user}\Documents\`
- Program Files: `C:\Program Files\Waypoint\` (requires admin)
- Custom folder: `C:\Tools\`, `D:\Apps\`, etc.

❌ **Bad locations:**
- Temp folder (automatic from "Open")
- Downloads folder (can be cleaned)
- Recycle Bin
- OneDrive/Dropbox (sync conflicts)

## Testing

### Test Case 1: Run from Temp (Open)
1. Download waypoint.exe
2. Click "Open" (not Save)
3. Check for updates
4. **Expected**: Warning displayed, update blocked with clear message

### Test Case 2: Run from Desktop (Save)
1. Download waypoint.exe
2. Click "Save As" → Desktop
3. Run from Desktop
4. Check for updates
5. **Expected**: Update succeeds, persists after restart

### Test Case 3: Run from Program Files
1. Copy waypoint.exe to `C:\Program Files\Waypoint\`
2. Run as administrator
3. Update
4. **Expected**: Update succeeds (with UAC prompt if needed)

## Files Modified
- `version_checker.py` - Added temp detection and blocking
- `app.py` - Added warning to update check UI

## Commits
- 3b3d436: Fix update failure when running from temp directory
- 92accbf: Bump version to 1.4.6

## Release
- **Version**: v1.4.6
- **Tag**: v1.4.6
- **Build**: Successful (~1m 10s)
- **Assets**: waypoint.exe, waypoint-portable.zip
- **Release URL**: https://github.com/mikejsmith1985/jira-automation/releases/tag/v1.4.6

## User Instructions

### For Users Experiencing Update Issues:

1. **Save the EXE to a permanent location:**
   - Download waypoint.exe from GitHub
   - Click "Save As" (not "Open")
   - Save to Desktop or create a folder like `C:\Apps\Waypoint\`

2. **Run from that permanent location:**
   - Navigate to where you saved it
   - Double-click to run
   - Do NOT run from temp folder

3. **Now updates will work:**
   - Check for updates
   - Click "Update"
   - App will restart with new version
   - Update persists across restarts

### Quick Check: Am I Running from Temp?
Look at the window title or diagnostics - if exe path contains:
- `\Temp\`
- `\MicrosoftEdgeDownloads\`
- `\AppData\Local\Temp\`

You're running from temp! Save to permanent location.

## Impact
- **Severity**: Medium (updates failed but app still functional)
- **Users Affected**: Anyone who clicked "Open" instead of "Save"
- **Fix**: Prevents failed updates with clear user instructions

## Status
✅ v1.4.6 released
✅ Update blocking implemented
✅ User guidance provided
✅ All changes committed and pushed
