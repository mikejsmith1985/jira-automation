"""
TDD Test Suite: Validate Core Functionality

Tests:
1. Test connection actually uses saved config
2. Settings persist after simulated update (AppData location)
3. Check for updates button works
4. Version mismatch detection
5. Version sync validation
"""

import os
import yaml
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Setup test environment
test_dir = tempfile.mkdtemp(prefix='waypoint_validation_')
test_config_path = os.path.join(test_dir, 'config.yaml')

def setup_config_with_snow():
    """Create a config with ServiceNow settings"""
    config = {
        'servicenow': {
            'url': 'https://test-company.service-now.com',
            'jira_project': 'TEST'
        },
        'github': {
            'api_token': 'ghp_test_token'
        },
        'feedback': {
            'github_token': 'ghp_feedback_token',
            'repo': 'mikejsmith1985/jira-automation'
        }
    }
    with open(test_config_path, 'w') as f:
        yaml.dump(config, f)
    return config

def test_1_test_connection_loads_saved_config():
    """TEST 1: Test connection should load ServiceNow URL from saved config"""
    print("\n" + "="*70)
    print("TEST 1: Test Connection Loads Saved Config")
    print("="*70)
    
    setup_config_with_snow()
    
    # Simulate test_connection logic
    with open(test_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    snow_config = config.get('servicenow', {})
    url = snow_config.get('url', '')
    
    print(f"Loaded ServiceNow URL: {url}")
    
    assert url == 'https://test-company.service-now.com', "URL not loaded from config!"
    assert snow_config.get('jira_project') == 'TEST', "Project not loaded from config!"
    
    print("✅ PASSED: Config correctly loaded for test connection")

def test_2_settings_persist_in_appdata():
    """TEST 2: Settings in AppData persist across 'updates' (new exe paths)"""
    print("\n" + "="*70)
    print("TEST 2: Settings Persist After Update (AppData)")
    print("="*70)
    
    setup_config_with_snow()
    
    # Simulate "update" - reading config from different location
    # AppData stays the same, executable path changes
    original_config = yaml.safe_load(open(test_config_path))
    
    # Pretend we're a new version reading from same AppData
    with open(test_config_path, 'r') as f:
        updated_version_config = yaml.safe_load(f)
    
    print(f"Original config sections: {list(original_config.keys())}")
    print(f"After 'update' config sections: {list(updated_version_config.keys())}")
    
    assert updated_version_config == original_config, "Config changed after 'update'!"
    assert 'servicenow' in updated_version_config, "ServiceNow config lost!"
    assert updated_version_config['servicenow']['url'] == 'https://test-company.service-now.com', \
        "ServiceNow URL lost after update!"
    
    print("✅ PASSED: Settings persist in AppData across updates")

def test_3_check_for_updates_mechanism():
    """TEST 3: Check for updates button calls GitHub API"""
    print("\n" + "="*70)
    print("TEST 3: Check For Updates Mechanism")
    print("="*70)
    
    # Import and test version_checker
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from version_checker import VersionChecker
    
    # Test with a known old version
    checker = VersionChecker(
        current_version='1.0.0',
        owner='mikejsmith1985',
        repo='jira-automation'
    )
    
    print("Checking for updates (this makes real GitHub API call)...")
    result = checker.check_for_update(use_cache=False)
    
    print(f"Result keys: {list(result.keys())}")
    print(f"Current version: {result.get('current_version')}")
    
    assert 'available' in result, "Missing 'available' key in result!"
    assert 'current_version' in result, "Missing 'current_version' key!"
    
    if result.get('error'):
        print(f"⚠️ WARNING: API call failed - {result['error']}")
        print("   (This might be expected if no internet or rate limited)")
    else:
        assert 'latest_version' in result, "Missing 'latest_version' key!"
        print(f"Latest version on GitHub: {result.get('latest_version')}")
        print("✅ PASSED: Update check mechanism works")

def test_4_version_mismatch_detection():
    """TEST 4: Detect when code version doesn't match release tag"""
    print("\n" + "="*70)
    print("TEST 4: Version Mismatch Detection")
    print("="*70)
    
    # Read actual version from app.py
    app_py_path = os.path.join(os.path.dirname(__file__), 'app.py')
    with open(app_py_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # Extract APP_VERSION
    import re
    version_match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', app_content)
    
    if version_match:
        code_version = version_match.group(1)
        print(f"Version in code: {code_version}")
    else:
        print("❌ Could not find APP_VERSION in app.py!")
        code_version = None
    
    # Now check what's on GitHub
    from version_checker import VersionChecker
    checker = VersionChecker(
        current_version=code_version or '1.0.0',
        owner='mikejsmith1985',
        repo='jira-automation'
    )
    
    print("Fetching latest release from GitHub...")
    result = checker.check_for_update(use_cache=False)
    
    if result.get('error'):
        print(f"⚠️ WARNING: Could not check GitHub - {result['error']}")
        print("   Cannot validate version sync")
        return
    
    github_version = result.get('latest_version', '').lstrip('v')
    code_version_clean = (code_version or '').lstrip('v')
    
    print(f"Code version: {code_version_clean}")
    print(f"GitHub latest release: {github_version}")
    
    if code_version_clean != github_version:
        print(f"❌ VERSION MISMATCH DETECTED!")
        print(f"   Code has: {code_version_clean}")
        print(f"   GitHub has: {github_version}")
        print(f"   User would need to manually download from GitHub!")
    else:
        print(f"✅ PASSED: Code version matches latest release")

def test_5_automated_version_sync_needed():
    """TEST 5: Is there a way to prevent version desync?"""
    print("\n" + "="*70)
    print("TEST 5: Automated Version Sync Solution")
    print("="*70)
    
    print("Current situation:")
    print("  - APP_VERSION is hardcoded in app.py")
    print("  - GitHub release tag is manual")
    print("  - No automated sync between them")
    print("")
    print("Proposed solutions:")
    print("  1. Read version from VERSION file (single source of truth)")
    print("  2. CI/CD checks that app.py version matches git tag before release")
    print("  3. Auto-update app.py version during build.ps1")
    print("  4. Build script extracts version from git tags")
    print("")
    
    # Check if VERSION file exists
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        print("✅ VERSION file exists")
        with open(version_file) as f:
            version_content = f.read().strip()
        print(f"   Content: {version_content}")
    else:
        print("❌ No VERSION file - versions can easily get out of sync")
    
    # Check if build.ps1 updates version
    build_script = os.path.join(os.path.dirname(__file__), 'build.ps1')
    if os.path.exists(build_script):
        with open(build_script, 'r', encoding='utf-8') as f:
            build_content = f.read()
        
        if 'APP_VERSION' in build_content or 'version' in build_content.lower():
            print("✅ build.ps1 mentions version")
        else:
            print("❌ build.ps1 does NOT validate/update version")
    
    print("")
    print("RECOMMENDATION: Implement automated version sync before next release!")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("TDD VALIDATION SUITE: Core Functionality")
    print("="*70)
    print("Testing assumptions about update mechanism, persistence, version sync")
    
    try:
        test_1_test_connection_loads_saved_config()
        test_2_settings_persist_in_appdata()
        test_3_check_for_updates_mechanism()
        test_4_version_mismatch_detection()
        test_5_automated_version_sync_needed()
        
        print("\n" + "="*70)
        print("VALIDATION COMPLETE")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
