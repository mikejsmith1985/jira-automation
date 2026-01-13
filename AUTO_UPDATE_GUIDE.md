# Auto-Update Feature - Quick Reference

## Overview
Replaced the non-functional "Account Management" button with an auto-update system inspired by Minecraft Forge. No login required - uses GitHub's public API.

## Location
**Sidebar** → Bottom-left corner (where "Account" used to be)

## How to Use

### Check for Updates
1. Click the **"Check Updates"** card in sidebar
2. Shows current version (e.g., "v1.2.10")
3. App queries GitHub releases
4. One of three outcomes:

#### ✅ Up to Date
- Icon: ✅
- Text: "Up to Date ✓"
- Notification: "You're running the latest version"

#### 🆕 Update Available
- Icon: 🆕
- Text: "Update Available!"
- Version: "1.2.10 → 1.2.11"
- Dialog appears with:
  - Current vs latest version
  - File size (MB)
  - Published date
  - Release notes preview
  - "Do you want to download and install?"

#### ❌ Check Failed
- Icon: ❌
- Text: "Check Failed"
- Notification shows error
- Automatically resets after 3 seconds

### Apply Update
1. Confirm dialog: Click "OK"
2. Status changes to "Updating..."
3. Icon: ⬇️
4. Progress notification shown
5. When complete:
   - Alert: "Update downloaded successfully!"
   - App automatically closes
   - Batch script runs in background:
     - Waits 2 seconds for app to close
     - Copies new .exe over old one
     - Restarts application
     - Deletes itself
6. App launches with new version

## Technical Details

### Version Checking
- **API**: `GET https://api.github.com/repos/mikejsmith1985/jira-automation/releases/latest`
- **Comparison**: Uses `packaging` library to compare semantic versions
- **Caching**: Results cached for 1 hour to avoid rate limits
- **Asset Detection**: Looks for `.exe` files or filenames containing "windows"

### Download & Apply
- **Temp Storage**: Downloads to `%TEMP%\waypoint_update.exe`
- **Batch Script**: Creates `%TEMP%\update_waypoint.bat`
- **Safety**: Script validates copy success before restarting
- **Cleanup**: Batch script deletes downloaded .exe and itself

### Batch Script Logic
```batch
@echo off
echo Waiting for Waypoint to close...
timeout /t 2 /nobreak >nul
echo Applying update...
copy /Y "temp_update.exe" "current_waypoint.exe"
if errorlevel 1 (
    echo Update failed!
    pause
    exit
)
echo Update complete! Restarting...
timeout /t 1 /nobreak >nul
start "" "current_waypoint.exe"
del "temp_update.exe"
del "%~f0"  # Delete self
```

## API Endpoints

### Check for Updates
```http
POST /api/updates/check
```

**Response:**
```json
{
  "success": true,
  "update_info": {
    "available": true,
    "current_version": "1.2.10",
    "latest_version": "v1.2.11",
    "release_notes": "## New Features\n- Auto-update\n- ...",
    "download_url": "https://github.com/.../waypoint.exe",
    "published_at": "2026-01-13T18:00:00Z",
    "asset_name": "waypoint.exe",
    "asset_size": 52428800
  }
}
```

### Apply Update
```http
POST /api/updates/apply
Content-Type: application/json

{
  "download_url": "https://github.com/.../waypoint.exe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Update downloaded. Application will restart...",
  "restart_required": true
}
```

## UI States

| State | Icon | Text | User Action |
|-------|------|------|-------------|
| **Default** | 🔄 | Check Updates | Click to check |
| **Checking** | ⏳ | Checking... | Wait |
| **Available** | 🆕 | Update Available! | Dialog appears |
| **Up-to-date** | ✅ | Up to Date ✓ | None (auto-reset) |
| **Downloading** | ⬇️ | Updating... | Wait |
| **Restarting** | 🔄 | Restarting... | App closes |
| **Failed** | ❌ | Check/Update Failed | Auto-reset after 3s |

## Error Handling

### Network Issues
- **Symptom**: "Check Failed" with network error
- **Cause**: No internet or GitHub unreachable
- **Solution**: Check internet, try again

### Rate Limiting
- **Symptom**: "GitHub API rate limit exceeded"
- **Cause**: Too many requests (60/hour for unauthenticated)
- **Solution**: Wait 1 hour, use cache

### No Releases
- **Symptom**: "No releases found"
- **Cause**: Repository has no published releases
- **Solution**: Wait for first release to be published

### Download Failure
- **Symptom**: "Update failed" after confirming
- **Cause**: Download interrupted, disk full, permissions
- **Solution**: Check disk space, permissions, retry

### Update Script Failure
- **Symptom**: App doesn't restart after update
- **Cause**: Batch script failed (file locked, permissions)
- **Solution**: Manually close app, run `%TEMP%\update_waypoint.bat`

## Comparison to Forge

| Feature | Forge | Waypoint |
|---------|-------|----------|
| **Check for updates** | ✓ Automatic on launch | ✓ Manual on click |
| **Notification** | ✓ Flashing icon | ✓ Dialog with details |
| **Release notes** | ✓ In changelog tab | ✓ In dialog preview |
| **Download** | ❌ Manual link | ✅ Automatic |
| **Apply update** | ❌ Manual install | ✅ Automatic + restart |
| **Rollback** | ❌ Not supported | ❌ Not supported (yet) |

## Future Enhancements

Potential improvements:
- [ ] Auto-check on startup (like Forge)
- [ ] Background update checks
- [ ] Update notifications in UI
- [ ] Rollback to previous version
- [ ] Beta/pre-release opt-in
- [ ] Update history/changelog viewer
- [ ] Pause/resume downloads
- [ ] Update scheduling (install later)

## Security Considerations

✅ **Safe:**
- Uses official GitHub API
- Only downloads from github.com domain
- Validates file exists before replacing
- No code execution during download
- Batch script is simple and inspectable

⚠️ **Note:**
- No signature verification (Windows may show warning)
- Trust based on GitHub source
- User must confirm before download
- Admin rights may be needed if installed to Program Files

## Troubleshooting

### Update Check Never Completes
1. Check console for errors (F12)
2. Verify internet connection
3. Try manual check: Visit https://github.com/mikejsmith1985/jira-automation/releases

### App Doesn't Restart After Update
1. Check Task Manager - kill any lingering waypoint.exe processes
2. Navigate to waypoint.exe location
3. Check if new file is there (check Properties → Details → Version)
4. Manually run waypoint.exe

### Want to Skip an Update
- Just click "Cancel" in the dialog
- Update won't be applied
- Can check again later when ready

### Stuck on Old Version
1. Go to Settings tab
2. Check current version displayed
3. Manually download from GitHub releases page
4. Replace waypoint.exe manually
5. Restart app

---

**Generated:** 2026-01-13  
**Feature:** Auto-Update  
**Commit:** 8aedcc8  
**Inspired By:** Minecraft Forge update checker
