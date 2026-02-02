"""
TDD Test Suite 1: ServiceNow Connection Error Handling

Tests all error scenarios for SNOW connection to ensure proper error messages.
Write tests FIRST, then implement fixes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch, MagicMock
import tempfile
import yaml

def test_1_snow_connection_no_browser():
    """TEST 1: SNOW connection fails gracefully when browser not initialized"""
    print("\n" + "="*70)
    print("TEST 1: SNOW Connection - No Browser")
    print("="*70)
    
    # Simulate the actual handler call with driver=None
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    # Mock global driver as None
    with patch('app.driver', None):
        result = app.SyncHandler.handle_test_snow_connection(handler)
    
    print(f"Result: {result}")
    
    assert result['success'] == False, "Should fail when browser not initialized"
    assert 'error' in result, "Should include error message"
    error_msg = result['error'].lower()
    assert 'browser' in error_msg or 'driver' in error_msg or 'selenium' in error_msg, \
        f"Error should mention browser/driver, got: {result['error']}"
    
    print("PASSED: Returns clear error when browser not initialized")

def test_2_snow_connection_no_config():
    """TEST 2: SNOW connection fails when config missing servicenow section"""
    print("\n" + "="*70)
    print("TEST 2: SNOW Connection - No Config")
    print("="*70)
    
    # Create temp config without servicenow section
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.yaml')
    
    config = {
        'jira': {'base_url': 'https://test.atlassian.net'},
        'github': {'api_token': 'test'}
        # No servicenow section
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    # Mock driver and DATA_DIR
    mock_driver = Mock()
    with patch('app.driver', mock_driver), \
         patch('app.DATA_DIR', temp_dir):
        result = app.SyncHandler.handle_test_snow_connection(handler)
    
    print(f"Result: {result}")
    
    assert result['success'] == False, "Should fail when config missing"
    assert 'error' in result, "Should include error message"
    error_msg = result['error'].lower()
    assert 'not configured' in error_msg or 'url' in error_msg or 'config' in error_msg, \
        f"Error should mention configuration issue, got: {result['error']}"
    
    print("PASSED: Returns clear error when config missing")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_3_snow_connection_empty_url():
    """TEST 3: SNOW connection fails when URL is empty string"""
    print("\n" + "="*70)
    print("TEST 3: SNOW Connection - Empty URL")
    print("="*70)
    
    # Create temp config with empty URL
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.yaml')
    
    config = {
        'servicenow': {
            'url': '',  # Empty!
            'jira_project': 'TEST'
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    mock_driver = Mock()
    with patch('app.driver', mock_driver), \
         patch('app.DATA_DIR', temp_dir):
        result = app.SyncHandler.handle_test_snow_connection(handler)
    
    print(f"Result: {result}")
    
    assert result['success'] == False, "Should fail when URL is empty"
    assert 'error' in result, "Should include error message"
    error_msg = result['error'].lower()
    assert 'url' in error_msg or 'not configured' in error_msg, \
        f"Error should mention URL issue, got: {result['error']}"
    
    print("PASSED: Returns clear error when URL is empty")
    
    import shutil
    shutil.rmtree(temp_dir)

def test_4_snow_connection_invalid_url_format():
    """TEST 4: SNOW connection validates URL format"""
    print("\n" + "="*70)
    print("TEST 4: SNOW Connection - Invalid URL Format")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.yaml')
    
    config = {
        'servicenow': {
            'url': 'not-a-valid-url',  # Invalid format
            'jira_project': 'TEST'
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    mock_driver = Mock()
    with patch('app.driver', mock_driver), \
         patch('app.DATA_DIR', temp_dir):
        result = app.SyncHandler.handle_test_snow_connection(handler)
    
    print(f"Result: {result}")
    
    # Should either fail or attempt connection
    # If it fails, error should be clear
    if not result['success']:
        error_msg = result['error'].lower()
        # Error should be informative (not generic Python traceback)
        assert len(result['error']) < 200, f"Error too verbose: {result['error'][:200]}"
        print(f"PASSED: Clear error for invalid URL: {result['error']}")
    else:
        print("WARNING: Did not validate URL format (may fail later)")
    
    import shutil
    shutil.rmtree(temp_dir)

def test_5_snow_connection_selenium_exception():
    """TEST 5: SNOW connection handles Selenium exceptions gracefully"""
    print("\n" + "="*70)
    print("TEST 5: SNOW Connection - Selenium Exception")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.yaml')
    
    config = {
        'servicenow': {
            'url': 'https://test.service-now.com',
            'jira_project': 'TEST'
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    import app
    handler = Mock()
    handler.__dict__.update(app.SyncHandler.__dict__)
    
    # Mock driver that raises exception
    mock_driver = Mock()
    mock_driver.get.side_effect = Exception("WebDriver error: connection refused")
    
    with patch('app.driver', mock_driver), \
         patch('app.DATA_DIR', temp_dir):
        result = app.SyncHandler.handle_test_snow_connection(handler)
    
    print(f"Result: {result}")
    
    assert result['success'] == False, "Should fail when Selenium raises exception"
    assert 'error' in result, "Should include error message"
    # Error should be user-friendly, not a full Python traceback
    assert len(result['error']) < 300, f"Error too verbose (likely traceback): {result['error'][:300]}"
    print(f"PASSED: Handles Selenium exception gracefully")
    
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("TDD TEST SUITE: ServiceNow Connection Error Handling")
    print("="*70)
    print("Testing error scenarios BEFORE implementing fixes")
    print("Expected: Most tests will FAIL initially (that's TDD!)")
    
    tests = [
        test_1_snow_connection_no_browser,
        test_2_snow_connection_no_config,
        test_3_snow_connection_empty_url,
        test_4_snow_connection_invalid_url_format,
        test_5_snow_connection_selenium_exception
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
        except Exception as e:
            failed += 1
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed > 0:
        print("\nExpected in TDD: Tests fail first, then we implement fixes")
        print("Next step: Implement error handling in handle_test_snow_connection()")
    else:
        print("\nAll tests passed! Error handling is working correctly.")
    
    sys.exit(0 if failed == 0 else 1)
