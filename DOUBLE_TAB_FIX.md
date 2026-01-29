# Double Tab Launch Fix

**Issue**: When running the compiled waypoint.exe, the app launches in 2 browser tabs instead of 1.

**Date**: January 29, 2026

---

## Root Causes Identified

1. **No duplicate call protection** - `open_browser()` could potentially be called multiple times
2. **Browser new parameter** - Using `new=0` might cause double-opening in some Windows configurations  
3. **Multiple instance risk** - No protection against running multiple app instances

---

## Solutions Implemented

### 1. Browser Opening Protection (app.py)

**Added global flag**:
```python
browser_opened = False  # Flag to prevent double-opening
```

**Updated `open_browser()` function**:
```python
def open_browser():
    """Open default browser to the app"""
    global browser_opened
    if browser_opened:
        safe_print("[BROWSER] Already opened, skipping duplicate call")
        return
    browser_opened = True
    time.sleep(1.5)
    safe_print("[BROWSER] Opening browser at http://127.0.0.1:5000")
    # new=2 opens in a new tab (avoids potential double-open with new=0)
    try:
        webbrowser.open('http://127.0.0.1:5000', new=2)
    except Exception as e:
        safe_print(f"[WARN] Failed to open browser: {e}")
```

**Changes**:
- Global flag prevents function from running twice
- Changed `new=0` to `new=2` (explicit new tab)
- Added try/except for better error handling
- Added logging for debugging

---

### 2. Single Instance Protection (app.py)

**Added lock file mechanism**:
```python
if __name__ == '__main__':
    # Prevent multiple instances using a lock file
    lock_file = os.path.join(DATA_DIR, 'waypoint.lock')
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            import psutil
            if psutil.pid_exists(old_pid):
                safe_print(f"[ERROR] Another instance is already running (PID {old_pid})")
                safe_print("[INFO] If the app is not visible, delete waypoint.lock and try again")
                sys.exit(1)
        except:
            pass  # Lock file is stale or invalid, proceed
    
    # Write our PID to lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass
    
    try:
        # ... existing startup code ...
    finally:
        # Clean up lock file on exit
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass
```

**How it works**:
1. Checks for `waypoint.lock` file
2. If exists, reads PID and checks if process is running
3. If running, exits with error message
4. If stale, proceeds and creates new lock file
5. Cleans up lock file on exit

---

### 3. Added Dependencies

**requirements.txt**:
```
psutil==5.9.6
```

**build.ps1**:
```
"--hidden-import=psutil"
```

---

## Testing

### Before Fix
- Double-click waypoint.exe → Opens 2 tabs

### After Fix
- Double-click waypoint.exe → Opens 1 tab
- Try double-clicking again → Shows error: "Another instance is already running"
- Close app → Lock file cleaned up automatically

---

## Files Modified

1. **app.py**:
   - Added `browser_opened` global flag (line ~89)
   - Updated `open_browser()` function (lines ~5638-5651)
   - Added single instance protection (lines ~5681-5734)

2. **requirements.txt**:
   - Added `psutil==5.9.6`

3. **build.ps1**:
   - Added `--hidden-import=psutil` (line ~67)

---

## Behavior

### Normal Launch
```
[INIT] Created config.yaml at C:\...\config.yaml
[START] Waypoint starting...
[SERVER] http://127.0.0.1:5000
[BROWSER] Opening browser...
[BROWSER] Opening browser at http://127.0.0.1:5000
[WAIT] Starting server (this will block)...
```

### Duplicate Instance Attempt
```
[ERROR] Another instance is already running (PID 12345)
[INFO] If the app is not visible, delete waypoint.lock and try again
```

### Browser Already Opened (if somehow called twice)
```
[BROWSER] Already opened, skipping duplicate call
```

---

## Cleanup

The lock file `waypoint.lock` is automatically removed when:
- App exits normally
- App is terminated (via finally block)

If app crashes without cleanup, user can manually delete the lock file.

---

## Impact

✅ **Fixed**: App now opens in single browser tab  
✅ **Added**: Single instance protection  
✅ **Improved**: Better logging for debugging  
✅ **Robust**: Handles edge cases (stale locks, multiple clicks)

---

**Status**: ✅ Fixed - Ready for v1.2.34 release
