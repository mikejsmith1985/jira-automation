"""
E2E Test: Verify ServiceNow configuration through HTTP API
Tests the actual API endpoints that the frontend calls
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"
TEST_SNOW_URL = "https://test-company.service-now.com"
TEST_JIRA_PROJECT = "TESTPROJ"

def test_save_snow_config():
    """Test POST /api/snow-jira/save-config"""
    print("\n" + "="*70)
    print("E2E TEST: Save ServiceNow Config via API")
    print("="*70)
    
    payload = {
        'url': TEST_SNOW_URL,
        'jira_project': TEST_JIRA_PROJECT,
        'field_mapping': {
            'impact': 'customfield_10001',
            'urgency': 'customfield_10002'
        }
    }
    
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/snow-jira/save-config",
            json=payload,
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        result = response.json()
        
        if result.get('success'):
            print("✓ Save succeeded")
            return True
        else:
            print(f"❌ Save failed: {result.get('error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app - is it running on http://127.0.0.1:5000?")
        print("   Start the app first with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_snow_config():
    """Test GET /api/snow-jira/config"""
    print("\n" + "="*70)
    print("E2E TEST: Get ServiceNow Config via API")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/snow-jira/config",
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            config = result.get('config', {})
            url = config.get('url', '')
            project = config.get('jira_project', '')
            
            print(f"\nExtracted URL: '{url}'")
            print(f"Extracted Project: '{project}'")
            
            if url == TEST_SNOW_URL and project == TEST_JIRA_PROJECT:
                print("✓ Config matches what we saved")
                return True
            else:
                print(f"❌ Config mismatch!")
                print(f"   Expected URL: '{TEST_SNOW_URL}'")
                print(f"   Got URL: '{url}'")
                return False
        else:
            print(f"❌ Get failed: {result.get('error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_prb():
    """Test POST /api/snow-jira/validate-prb"""
    print("\n" + "="*70)
    print("E2E TEST: Validate PRB (will fail without driver, but tests config loading)")
    print("="*70)
    
    payload = {
        'prb_number': 'PRB0123456'
    }
    
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/snow-jira/validate-prb",
            json=payload,
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # We expect this to fail because driver isn't initialized or not logged in
        # But we can check if it's the URL config issue or driver issue
        error = result.get('error', '')
        
        if 'ServiceNow URL not configured' in error:
            print("❌ FAIL: Config wasn't loaded properly - URL is empty!")
            return False
        elif 'Browser not open' in error or 'driver' in error.lower():
            print("✓ PASS: Config loaded correctly (failed on driver, which is expected)")
            return True
        elif 'login' in error.lower():
            print("✓ PASS: Config loaded, navigated to SNOW (failed on login, which is expected)")
            return True
        else:
            print(f"⚠️  Unexpected error (but not config issue): {error}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("SERVICENOW E2E TEST SUITE")
    print("Requires app to be running on http://127.0.0.1:5000")
    print("="*70)
    
    # Test sequence
    tests = [
        ("Save Config", test_save_snow_config),
        ("Get Config", test_get_snow_config),
        ("Validate PRB", test_validate_prb),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        if not result:
            print(f"\n⚠️  Stopping tests - {test_name} failed")
            break
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - ServiceNow config flow is working correctly")
    else:
        print("\n❌ SOME TESTS FAILED - See details above")
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
