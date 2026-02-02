"""
Automatic version sync script
Extracts version from git tag and updates app.py

This runs automatically before build to ensure APP_VERSION matches the git tag.
"""

import re
import subprocess
import sys
import os

def get_latest_git_tag():
    """Get the latest git tag"""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=True
        )
        tag = result.stdout.strip()
        # Remove 'v' prefix if present
        version = tag.lstrip('v')
        return version
    except subprocess.CalledProcessError:
        # No tags yet
        return None
    except FileNotFoundError:
        print("ERROR: git not found in PATH")
        return None

def get_current_app_version():
    """Read APP_VERSION from app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return None

def update_app_version(new_version):
    """Update APP_VERSION in app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace APP_VERSION line
    updated = re.sub(
        r'(APP_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        rf'\g<1>{new_version}\g<2>',
        content
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    
    return True

def main():
    """Sync version from git tag to app.py"""
    print("Version Sync: Checking git tag...")
    
    git_version = get_latest_git_tag()
    if not git_version:
        print("WARNING: No git tags found. Using version from app.py.")
        return 0
    
    print(f"Latest git tag: v{git_version}")
    
    app_version = get_current_app_version()
    if not app_version:
        print("ERROR: Could not find APP_VERSION in app.py")
        return 1
    
    print(f"Current APP_VERSION: {app_version}")
    
    if app_version == git_version:
        print(f"✓ Version already in sync: {app_version}")
        return 0
    
    print(f"! Version mismatch detected!")
    print(f"  Git tag:     v{git_version}")
    print(f"  APP_VERSION: {app_version}")
    print(f"")
    print(f"Updating app.py to match git tag...")
    
    if update_app_version(git_version):
        print(f"✓ Updated APP_VERSION to {git_version}")
        
        # Verify the change
        new_version = get_current_app_version()
        if new_version == git_version:
            print(f"✓ Version sync complete")
            return 0
        else:
            print(f"ERROR: Verification failed. APP_VERSION is now {new_version}")
            return 1
    else:
        print(f"ERROR: Failed to update app.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
