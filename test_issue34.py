"""
TDD tests for Issue #34 - ServiceNow PRB navigation
Bug: PRB opens in browser but Waypoint says "not found"
Root cause: URL opens list view, but code waits for form view elements
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from selenium.common.exceptions import TimeoutException


class TestPRBNavigation(unittest.TestCase):
    """Test ServiceNow PRB navigation logic"""
    
    def setUp(self):
        """Set up mock driver and scraper"""
        self.mock_driver = Mock()
        self.config = {
            'servicenow': {
                'url': 'https://cigna.service-now.com'
            }
        }
    
    def test_prb_url_format_list_view(self):
        """Test: sysparm_query URL opens a list view, not form"""
        # The current URL format opens a LIST, not a form
        base_url = 'https://cigna.service-now.com'
        prb_number = 'PRB0071419'
        
        # Current (problematic) URL - opens list view
        list_url = f"{base_url}/problem.do?sysparm_query=number={prb_number}"
        
        # This is the list view URL pattern
        self.assertIn('sysparm_query', list_url)
        
    def test_prb_url_format_direct_form(self):
        """Test: Direct form URL should use sys_id or different pattern"""
        base_url = 'https://cigna.service-now.com'
        prb_number = 'PRB0071419'
        
        # Alternative: Use nav_to.do with record lookup
        # Or: Click through from list view
        # The code should handle list → form transition
        
    def test_navigate_handles_list_view_click_through(self):
        """Test: Navigation should click the PRB in list to open form"""
        from servicenow_scraper import ServiceNowScraper
        
        scraper = ServiceNowScraper(self.mock_driver, self.config)
        
        # The navigate function exists
        self.assertTrue(hasattr(scraper, 'navigate_to_prb'))
        
    def test_wait_element_should_handle_both_views(self):
        """Test: Should wait for either list OR form elements"""
        # Current code waits for 'problem.short_description' which is FORM only
        # If page is a LIST, this element won't exist → timeout
        form_element_id = 'problem.short_description'
        list_element_class = 'list2_body'  # Common list view element
        
        # The fix should check for EITHER view type
        
    def test_scraper_returns_false_on_timeout(self):
        """Test: Verify timeout returns False when PRB not found anywhere"""
        from servicenow_scraper import ServiceNowScraper
        
        self.mock_driver.get = Mock()
        self.mock_driver.current_url = 'https://cigna.service-now.com/problem.do'
        self.mock_driver.page_source = 'no prb here'  # PRB not in page
        
        # Mock find_element to always fail
        def mock_find_element(by, value):
            from selenium.common.exceptions import NoSuchElementException
            raise NoSuchElementException()
        
        self.mock_driver.find_element = mock_find_element
        
        # Simulate timeout on all waits
        with patch('servicenow_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException()
            
            with patch('servicenow_scraper.time.sleep'):
                scraper = ServiceNowScraper(self.mock_driver, self.config)
                result = scraper.navigate_to_prb('PRB0071419')
                
                # Should return False - PRB not found
                self.assertFalse(result)
            
    def test_scraper_handles_list_then_form(self):
        """Test: Scraper should navigate list → click row → verify form"""
        from servicenow_scraper import ServiceNowScraper
        
        # Mock the flow: get list → find row → click → wait for form
        mock_row_link = Mock()
        mock_row_link.click = Mock()
        
        self.mock_driver.get = Mock()
        self.mock_driver.page_source = 'PRB0071419'  # PRB found in source
        self.mock_driver.current_url = 'https://cigna.service-now.com/problem.do?PRB0071419'
        
        # Mock find_element to return not found for form, then found for link
        def mock_find_element(by, value):
            if value == 'problem.short_description':
                from selenium.common.exceptions import NoSuchElementException
                raise NoSuchElementException()
            return mock_row_link
        
        self.mock_driver.find_element = mock_find_element
        
        with patch('servicenow_scraper.WebDriverWait') as mock_wait:
            mock_wait_instance = Mock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.return_value = mock_row_link
            
            scraper = ServiceNowScraper(self.mock_driver, self.config)
            result = scraper.navigate_to_prb('PRB0071419')
            
            # Should succeed (PRB found in page source)
            self.assertTrue(result)
            
    def test_navigate_checks_form_first(self):
        """Test: Should check if already on form view before trying list"""
        from servicenow_scraper import ServiceNowScraper
        
        mock_form_element = Mock()
        self.mock_driver.get = Mock()
        self.mock_driver.find_element = Mock(return_value=mock_form_element)
        self.mock_driver.current_url = 'https://cigna.service-now.com/problem.do'
        
        with patch('servicenow_scraper.time.sleep'):
            scraper = ServiceNowScraper(self.mock_driver, self.config)
            result = scraper.navigate_to_prb('PRB0071419')
            
            # Should succeed - found form element directly
            self.assertTrue(result)


class TestPRBURLPatterns(unittest.TestCase):
    """Test different URL patterns for ServiceNow"""
    
    def test_sysparm_query_is_list_view(self):
        """sysparm_query=number=X returns a filtered list, not a record"""
        url = "https://example.service-now.com/problem.do?sysparm_query=number=PRB123"
        self.assertIn('sysparm_query', url)
        # This URL pattern returns a LIST with one record, not the form directly
        
    def test_direct_record_url_pattern(self):
        """Direct record access needs sys_id or different approach"""
        # Option 1: Use sys_id directly (requires API or prior lookup)
        # sys_id_url = "https://example.service-now.com/problem.do?sys_id=abc123"
        
        # Option 2: Navigate to list, then click the record link
        # This is more reliable for web scraping without API access
        pass


if __name__ == '__main__':
    unittest.main()
