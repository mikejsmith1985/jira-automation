# Config Persistence Fix - Summary

## Problem
Users had to re-enter their Jira and GitHub info every time they ran a new version of the app, even though they saved their configuration.

## Root Cause
The app was storing `config.yaml` and `feedback.db` in the **executable directory** (`DATA_DIR = directory of .exe`). When users downloaded a new version to a new location, a fresh config file was created.

## Solution
Changed `DATA_DIR` to use a **persistent user-specific location**:

### For Executable (Frozen) Mode:
```
%APPDATA%\Waypoint\
```
Example: `C:\Users\YourName\AppData\Roaming\Waypoint\`

### For Script Mode (Development):
```
Script directory (unchanged)
```

## Changes Made

### 1. Updated `get_data_dir()` function (line 44-54)
```python
def get_data_dir():
    """Get writable data directory for config and user data"""
    if getattr(sys, 'frozen', False):
        # Running as executable - use AppData for persistence across versions
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'Waypoint')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    else:
        # Running as script - use script directory
        return os.path.dirname(os.path.abspath(__file__))
```

### 2. Added Migration Logic (line 5779-5792)
When the app starts as an executable:
- Checks if config exists in the **new location** (`%APPDATA%\Waypoint\`)
- If not, looks for config in the **old location** (exe directory)
- If found in old location, **copies it to the new location**
- Logs the migration so user is aware

### 3. Updated FeedbackDB Path (line 87)
```python
feedback_db = FeedbackDB(db_path=os.path.join(DATA_DIR, 'feedback.db'))
```
Now stores feedback database in the same persistent location.

### 4. Added Logging (line 5755)
```python
safe_print(f"[CONFIG] Data directory: {DATA_DIR}")
```
Users can now see where their data is stored.

## Benefits

✅ **Persistence Across Versions** - Config survives app updates  
✅ **Automatic Migration** - Old config automatically copied to new location  
✅ **Clear Logging** - Users know where data is stored  
✅ **Standard Location** - Follows Windows conventions for app data  
✅ **No User Action Required** - Migration happens automatically

## User Experience

### First Run (After Update)
```
[CONFIG] Data directory: C:\Users\YourName\AppData\Roaming\Waypoint
[MIGRATE] Copied config from old location to C:\Users\YourName\AppData\Roaming\Waypoint\config.yaml
[INFO] Config is now stored in C:\Users\YourName\AppData\Roaming\Waypoint for persistence across versions
[START] Waypoint starting...
```

### Subsequent Runs
```
[CONFIG] Data directory: C:\Users\YourName\AppData\Roaming\Waypoint
[START] Waypoint starting...
```
Config is loaded from persistent location, no re-entry needed.

## Files Affected
- `config.yaml` - User configuration (Jira, GitHub, integrations)
- `feedback.db` - Feedback submission history
- `jira-sync.log` - Application logs
- `waypoint.lock` - Process lock file

## Testing Notes
- Old configs in exe directory are **copied, not moved** (safe)
- Migration only runs once (when new location is empty)
- Script mode unchanged (still uses script directory)

## Related Issues
Fixes user-reported issue: "every time I run a new version of the app I have to re-enter my jira and github info for feedback submission despite saving the issues"
