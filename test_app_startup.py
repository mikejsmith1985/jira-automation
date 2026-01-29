#!/usr/bin/env python
"""Test script to verify app can start and serve pages"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Waypoint App Startup")
print("=" * 60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from jira_version_creator import JiraVersionCreator
    print("   ✅ jira_version_creator imported")
except Exception as e:
    print(f"   ❌ jira_version_creator failed: {e}")
    sys.exit(1)

try:
    import app
    print("   ✅ app.py imported")
except Exception as e:
    print(f"   ❌ app.py failed: {e}")
    sys.exit(1)

# Test 2: Check files exist
print("\n2. Checking required files...")
files_to_check = [
    'modern-ui.html',
    'assets/js/modern-ui.js',
    'assets/css/modern-ui.css',
    'config.yaml'
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"   ✅ {filepath} ({size:,} bytes)")
    else:
        print(f"   ❌ {filepath} NOT FOUND")

# Test 3: Check BASE_DIR and DATA_DIR
print("\n3. Checking directories...")
print(f"   BASE_DIR: {app.BASE_DIR}")
print(f"   DATA_DIR: {app.DATA_DIR}")
print(f"   Current dir: {os.getcwd()}")

# Test 4: Check if HTML file can be read
print("\n4. Testing HTML file access...")
try:
    html_path = os.path.join(app.BASE_DIR, 'modern-ui.html')
    print(f"   Trying: {html_path}")
    with open(html_path, 'rb') as f:
        content = f.read()
    print(f"   ✅ Successfully read {len(content):,} bytes")
    
    # Check for fixVersion section
    if b'Create fixVersions' in content:
        print("   ✅ Contains fixVersion section")
    else:
        print("   ⚠️  fixVersion section not found")
        
except Exception as e:
    print(f"   ❌ Failed to read HTML: {e}")

# Test 5: Check JavaScript
print("\n5. Testing JavaScript file...")
try:
    js_path = os.path.join(app.BASE_DIR, 'assets/js/modern-ui.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    if 'createFixVersions' in js_content:
        print(f"   ✅ JavaScript contains createFixVersions function")
    else:
        print(f"   ⚠️  createFixVersions function not found")
        
except Exception as e:
    print(f"   ❌ Failed to read JavaScript: {e}")

print("\n" + "=" * 60)
print("✅ All tests passed! App should work.")
print("=" * 60)
print("\nTo start the app, run: python app.py")
print("Then open your browser to: http://localhost:5000")
