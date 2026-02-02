"""
TDD Tests for ServiceNow Configuration Flow - Issue #32
Following @.github/copilot-instructions.md

Test the complete flow:
1. Frontend sends data to backend
2. Backend saves to config.yaml
3. Backend loads config and creates SnowJiraSync
4. ServiceNowScraper reads URL from config
5. URL is used correctly for navigation
"""
import os
import sys
import yaml
import json
import tempfile
import shutil
from pathlib import Path

# Test configuration
TEST_SNOW_URL = "https://test-company.service-now.com"
TEST_JIRA_PROJECT = "TESTPROJ"

class TestServiceNowConfigFlow:
    """Test the complete ServiceNow configuration save/load flow"""
    
    def setup(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
        
        # Create minimal config
        self.config = {
            'servicenow': {},
            'jira': {},
            'github': {}
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f)
        
        print(f"✓ Test environment created at {self.test_dir}")
    
    def teardown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        print(f"✓ Test environment cleaned up")
    
    def test_1_save_config_with_valid_data(self):
        """Test saving ServiceNow config with valid URL and project"""
        print("\n" + "="*70)
        print("TEST 1: Save Config with Valid Data")
        print("="*70)
        
        # Simulate frontend sending data
        incoming_data = {
            'url': TEST_SNOW_URL,
            'jira_project': TEST_JIRA_PROJECT,
            'field_mapping': {
                'impact': 'customfield_10001',
                'urgency': 'customfield_10002'
            }
        }
        
        print(f"Input data: {json.dumps(incoming_data, indent=2)}")
        
        # Load config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Update servicenow section (mimicking backend handler)
        if 'servicenow' not in config:
            config['servicenow'] = {}
        
        config['servicenow'].update(incoming_data)
        
        # Save config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("✓ Config saved")
        
        # Verify it was saved correctly
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_config = yaml.safe_load(f)
        
        print(f"\nSaved config: {json.dumps(saved_config.get('servicenow', {}), indent=2)}")
        
        assert 'servicenow' in saved_config, "servicenow key missing"
        assert saved_config['servicenow']['url'] == TEST_SNOW_URL, f"URL mismatch: {saved_config['servicenow']['url']}"
        assert saved_config['servicenow']['jira_project'] == TEST_JIRA_PROJECT, f"Project mismatch"
        
        print("✓ All assertions passed")
        return saved_config
    
    def test_2_load_config_and_extract_url(self):
        """Test loading config and extracting URL (like ServiceNowScraper does)"""
        print("\n" + "="*70)
        print("TEST 2: Load Config and Extract URL")
        print("="*70)
        
        # First save a config
        saved_config = self.test_1_save_config_with_valid_data()
        
        # Now simulate loading it (like ServiceNowScraper.__init__)
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"\nLoaded config keys: {list(config.keys())}")
        print(f"servicenow config: {config.get('servicenow', {})}")
        
        # Extract URL the same way ServiceNowScraper does
        base_url = config.get('servicenow', {}).get('url', '')
        
        print(f"\nExtracted base_url: '{base_url}'")
        print(f"Expected: '{TEST_SNOW_URL}'")
        print(f"Match: {base_url == TEST_SNOW_URL}")
        
        assert base_url == TEST_SNOW_URL, f"URL extraction failed: got '{base_url}', expected '{TEST_SNOW_URL}'"
        assert base_url, "URL is empty!"
        
        print("✓ URL extracted correctly")
        return base_url
    
    def test_3_url_format_for_prb_navigation(self):
        """Test that URL can be used to build PRB navigation URL"""
        print("\n" + "="*70)
        print("TEST 3: Build PRB Navigation URL")
        print("="*70)
        
        base_url = self.test_2_load_config_and_extract_url()
        
        # Simulate navigate_to_prb logic
        prb_number = "PRB0123456"
        
        if not base_url:
            print("❌ FAIL: base_url is empty")
            return False
        
        prb_url = f"{base_url}/problem.do?sysparm_query=number={prb_number}"
        
        print(f"\nPRB URL constructed: {prb_url}")
        
        expected_url = f"{TEST_SNOW_URL}/problem.do?sysparm_query=number={prb_number}"
        
        assert prb_url == expected_url, f"PRB URL mismatch"
        print("✓ PRB URL constructed correctly")
        
        return prb_url
    
    def test_4_actual_app_integration(self):
        """Test with actual app.py handler"""
        print("\n" + "="*70)
        print("TEST 4: Actual App Integration")
        print("="*70)
        
        # Temporarily override DATA_DIR
        import app
        original_data_dir = app.DATA_DIR
        app.DATA_DIR = self.test_dir
        
        try:
            # Create handler instance
            from http.server import BaseHTTPRequestHandler
            from io import BytesIO
            
            # Mock request/response
            class MockHandler:
                pass
            
            handler = MockHandler()
            
            # Import the actual handler method
            from app import SyncHandler
            
            # Call the save method with test data
            data = {
                'url': TEST_SNOW_URL,
                'jira_project': TEST_JIRA_PROJECT,
                'field_mapping': {}
            }
            
            print(f"Calling handle_save_snow_config with: {json.dumps(data, indent=2)}")
            
            # Create a real SyncHandler instance properly
            # We need to mock the BaseHTTPRequestHandler properly
            import socket
            mock_request = BytesIO()
            mock_client_address = ('127.0.0.1', 12345)
            mock_server = type('MockServer', (), {'server_address': ('127.0.0.1', 5000)})()
            
            handler_instance = SyncHandler(mock_request, mock_client_address, mock_server)
            result = handler_instance.handle_save_snow_config(data)
            
            print(f"\nResult: {json.dumps(result, indent=2)}")
            
            assert result['success'], f"Save failed: {result.get('error')}"
            
            # Verify it was actually saved
            with open(self.config_path, 'r', encoding='utf-8') as f:
                saved = yaml.safe_load(f)
            
            print(f"\nActual saved config: {json.dumps(saved.get('servicenow', {}), indent=2)}")
            
            assert saved['servicenow']['url'] == TEST_SNOW_URL
            print("✓ App integration test passed")
            
        finally:
            app.DATA_DIR = original_data_dir
    
    def test_5_servicenow_scraper_integration(self):
        """Test that ServiceNowScraper can read the saved config"""
        print("\n" + "="*70)
        print("TEST 5: ServiceNowScraper Integration")
        print("="*70)
        
        # Save config first
        self.test_1_save_config_with_valid_data()
        
        # Load config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Create ServiceNowScraper instance
        from servicenow_scraper import ServiceNowScraper
        
        # Mock driver
        class MockDriver:
            current_url = "https://test.service-now.com"
        
        scraper = ServiceNowScraper(MockDriver(), config)
        
        print(f"\nServiceNowScraper.base_url: '{scraper.base_url}'")
        print(f"Expected: '{TEST_SNOW_URL}'")
        
        assert scraper.base_url == TEST_SNOW_URL, f"ServiceNowScraper got wrong URL: '{scraper.base_url}'"
        assert scraper.base_url, "ServiceNowScraper base_url is empty!"
        
        print("✓ ServiceNowScraper integration test passed")

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*70)
    print("SERVICENOW CONFIGURATION TDD TEST SUITE")
    print("="*70)
    
    test_suite = TestServiceNowConfigFlow()
    test_suite.setup()
    
    try:
        test_suite.test_1_save_config_with_valid_data()
        test_suite.test_2_load_config_and_extract_url()
        test_suite.test_3_url_format_for_prb_navigation()
        test_suite.test_4_actual_app_integration()
        test_suite.test_5_servicenow_scraper_integration()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        return True
        
    except AssertionError as e:
        print("\n" + "="*70)
        print(f"❌ TEST FAILED: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        test_suite.teardown()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
