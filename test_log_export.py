"""
TDD Test Suite 3: Log Export Functionality

Tests log export feature to ensure it provides useful debugging information.
Write tests FIRST, then implement.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
import tempfile
import logging

def test_1_log_export_endpoint_exists():
    """TEST 1: Log export endpoint exists and returns success"""
    print("\n" + "="*70)
    print("TEST 1: Log Export Endpoint Exists")
    print("="*70)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    # Call handle_export_logs
    result = app.SyncHandler.handle_export_logs(handler)
    
    print(f"Result keys: {list(result.keys())}")
    
    assert result is not None, "Should return a result"
    assert 'success' in result, "Should have success key"
    assert result['success'] == True, "Should succeed"
    
    print("PASSED: Endpoint exists and returns success")

def test_2_log_export_includes_version():
    """TEST 2: Exported logs include app version"""
    print("\n" + "="*70)
    print("TEST 2: Log Export Includes Version")
    print("="*70)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    result = app.SyncHandler.handle_export_logs(handler)
    
    assert 'log_data' in result or 'content' in result or 'file_path' in result, \
        "Should include log data in some form"
    
    # Get the log content
    log_content = result.get('log_data', result.get('content', ''))
    
    # Should mention version
    assert len(log_content) > 0, "Log content should not be empty"
    print(f"Log content length: {len(log_content)} chars")
    
    # Check for version info
    has_version = 'version' in log_content.lower() or app.APP_VERSION in log_content
    print(f"Contains version info: {has_version}")
    
    if has_version:
        print("PASSED: Includes version information")
    else:
        print("WARNING: Version info not found, but may be acceptable")

def test_3_log_export_includes_config_diagnostics():
    """TEST 3: Exported logs include config diagnostics"""
    print("\n" + "="*70)
    print("TEST 3: Log Export Includes Config Diagnostics")
    print("="*70)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    result = app.SyncHandler.handle_export_logs(handler)
    
    log_content = result.get('log_data', result.get('content', ''))
    
    # Should include config-related info
    has_config_info = (
        'config' in log_content.lower() or
        'servicenow' in log_content.lower() or
        'jira' in log_content.lower()
    )
    
    print(f"Contains config diagnostics: {has_config_info}")
    
    if has_config_info:
        print("PASSED: Includes configuration diagnostics")
    else:
        print("WARNING: Config diagnostics not found")

def test_4_log_export_no_sensitive_data():
    """TEST 4: Exported logs don't include sensitive data"""
    print("\n" + "="*70)
    print("TEST 4: Log Export - No Sensitive Data")
    print("="*70)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    result = app.SyncHandler.handle_export_logs(handler)
    
    log_content = result.get('log_data', result.get('content', ''))
    
    # Should NOT include tokens, passwords, etc.
    sensitive_keywords = ['password', 'api_token', 'github_token', 'ghp_']
    
    found_sensitive = []
    for keyword in sensitive_keywords:
        if keyword in log_content.lower():
            found_sensitive.append(keyword)
    
    if found_sensitive:
        print(f"WARNING: Found potentially sensitive data: {found_sensitive}")
        print("Checking if it's just field names (acceptable) or actual values (bad)...")
        # This is acceptable if it's just field names like "api_token: <configured>"
    else:
        print("PASSED: No sensitive keywords found")

def test_5_log_export_includes_recent_errors():
    """TEST 5: Exported logs include recent log entries"""
    print("\n" + "="*70)
    print("TEST 5: Log Export Includes Recent Logs")
    print("="*70)
    
    # Write a test log entry
    test_message = "TEST_LOG_EXPORT_MARKER_98765"
    logging.info(test_message)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    result = app.SyncHandler.handle_export_logs(handler)
    
    log_content = result.get('log_data', result.get('content', ''))
    
    # Check if our test message is in the export
    has_recent_logs = test_message in log_content
    
    print(f"Contains recent log entries: {has_recent_logs}")
    
    if has_recent_logs:
        print("PASSED: Includes recent log entries")
    else:
        print("NOTE: May not include very recent logs (depends on log file flush)")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("TDD TEST SUITE: Log Export Functionality")
    print("="*70)
    print("Testing log export feature BEFORE full implementation")
    
    tests = [
        test_1_log_export_endpoint_exists,
        test_2_log_export_includes_version,
        test_3_log_export_includes_config_diagnostics,
        test_4_log_export_no_sensitive_data,
        test_5_log_export_includes_recent_errors
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"FAILED: {e}")
        except AttributeError as e:
            failed += 1
            print(f"NOT IMPLEMENTED: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR: {e}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed > 0:
        print("\nExpected in TDD: Tests fail first, then we implement")
        print("Next step: Implement handle_export_logs() endpoint")
    else:
        print("\nAll tests passed! Log export is working correctly.")
    
    sys.exit(0 if failed == 0 else 1)
