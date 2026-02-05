"""
Test the update mechanism locally
"""
import requests
import time
import os
import shutil

# Test setup
current_dir = r"C:\Users\mikej\Desktop\update-test"
update_file = r"C:\Users\mikej\Downloads\waypoint-update-v2.1.1.exe"
log_dir = os.path.join(os.environ['APPDATA'], 'Waypoint', 'diagnostics')

print("=" * 60)
print("LOCAL UPDATE TEST")
print("=" * 60)

# Step 1: Verify v2.1.0 is running
print("\n[1] Checking current version...")
try:
    response = requests.get("http://127.0.0.1:5000/api/version", timeout=3)
    version_data = response.json()
    print(f"    Current version: {version_data['version']}")
    if version_data['version'] != "2.1.0":
        print(f"    ERROR: Expected 2.1.0, got {version_data['version']}")
        exit(1)
except Exception as e:
    print(f"    ERROR: {e}")
    exit(1)

# Step 2: Copy update file to temp (simulate download)
print("\n[2] Simulating update download...")
import tempfile
temp_exe = os.path.join(tempfile.gettempdir(), 'waypoint_update.exe')
shutil.copy2(update_file, temp_exe)
print(f"    Copied to: {temp_exe}")

# Step 3: Trigger update via internal method (simulate the version_checker)
print("\n[3] Applying update using Forge pattern...")
current_exe = os.path.join(current_dir, "waypoint.exe")
backup_exe = current_exe + '.old'

try:
    # Remove old backup
    if os.path.exists(backup_exe):
        os.remove(backup_exe)
        print(f"    Removed old backup")
    
    # Rename current to backup
    os.rename(current_exe, backup_exe)
    print(f"    Backed up current exe")
    
    # Copy new to current location
    shutil.copy2(temp_exe, current_exe)
    print(f"    Installed new version")
    
    # Cleanup temp
    os.remove(temp_exe)
    print(f"    Cleaned up temp file")
    
    print("\n✓ Update applied successfully!")
    
except Exception as e:
    print(f"\n✗ Update failed: {e}")
    # Restore backup
    if not os.path.exists(current_exe) and os.path.exists(backup_exe):
        os.rename(backup_exe, current_exe)
        print(f"    Restored backup")
    exit(1)

# Step 4: Request app to restart
print("\n[4] Requesting app restart...")
try:
    # This will trigger the restart
    response = requests.post("http://127.0.0.1:5000/api/apply-update", 
                            json={"restart": True},
                            timeout=3)
    print(f"    Response: {response.json()}")
except Exception as e:
    print(f"    Request sent (app may have already exited): {e}")

# Wait for restart
print("\n[5] Waiting for app to restart...")
for i in range(10):
    time.sleep(1)
    try:
        response = requests.get("http://127.0.0.1:5000/api/version", timeout=1)
        version_data = response.json()
        print(f"    New version running: {version_data['version']}")
        
        if version_data['version'] == "2.1.1":
            print("\n" + "=" * 60)
            print("✓ UPDATE TEST PASSED!")
            print("=" * 60)
            exit(0)
        else:
            print(f"    WARNING: Expected 2.1.1, got {version_data['version']}")
    except:
        print(f"    Waiting... ({i+1}/10)")

print("\n" + "=" * 60)
print("✗ UPDATE TEST FAILED - App did not restart")
print("=" * 60)

# Check logs
print("\nChecking logs...")
if os.path.exists(log_dir):
    for log_file in os.listdir(log_dir):
        if log_file.endswith('.log') or log_file.endswith('.txt'):
            print(f"\nLast 20 lines of {log_file}:")
            log_path = os.path.join(log_dir, log_file)
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        print(f"  {line.rstrip()}")
            except:
                pass
