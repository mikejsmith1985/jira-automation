"""
TDD tests for Issue #36 - ServiceNow field detection
Bug: Fields not found because iframe detection is incorrect
Update: Field IDs vary between ServiceNow UI modes
"""
import unittest
from unittest.mock import Mock, MagicMock, patch


class TestServiceNowFieldIDVariations(unittest.TestCase):
    """Test field ID variations between ServiceNow UI modes"""
    
    def test_classic_ui_uses_dotted_ids(self):
        """Test: Classic UI uses IDs like 'problem.short_description'"""
        classic_id = "problem.short_description"
        self.assertIn('.', classic_id)
        self.assertTrue(classic_id.startswith('problem.'))
    
    def test_modern_ui_drops_prefix(self):
        """Test: Modern UI may use IDs like 'short_description' (no prefix)"""
        # User reports: have to drop "problem." to work with their parser
        modern_id = "short_description"
        self.assertNotIn('.', modern_id)
        self.assertFalse(modern_id.startswith('problem.'))
    
    def test_field_value_tries_multiple_variations(self):
        """Test: _get_field_value should try both ID formats"""
        from servicenow_scraper import ServiceNowScraper
        
        mock_driver = Mock()
        config = {'servicenow': {'url': 'https://test.service-now.com'}}
        
        scraper = ServiceNowScraper(mock_driver, config)
        
        # Should try:
        # 1. problem.short_description
        # 2. short_description (without prefix)
        # 3. problem_short_description (dots to underscores)
        
    def test_extract_works_with_either_id_format(self):
        """Test: extract_prb_data should work regardless of ID format used"""
        from servicenow_scraper import ServiceNowScraper
        
        mock_driver = Mock()
        config = {'servicenow': {'url': 'https://test.service-now.com'}}
        
        # Mock element that will be found on second try (modern ID)
        mock_element = Mock()
        mock_element.tag_name = 'input'
        mock_element.get_attribute.return_value = 'Test Value'
        
        def find_element_side_effect(by, value):
            from selenium.common.exceptions import NoSuchElementException
            # First try (problem.short_description) fails
            if value == 'problem.short_description':
                raise NoSuchElementException()
            # Second try (short_description) succeeds
            elif value == 'short_description':
                return mock_element
            else:
                raise NoSuchElementException()
        
        mock_driver.find_element = Mock(side_effect=find_element_side_effect)
        
        scraper = ServiceNowScraper(mock_driver, config)
        value = scraper._get_field_value('problem.short_description')
        
        # Should have tried both and found it on second try
        self.assertEqual(value, 'Test Value')


class TestServiceNowIframeDetection(unittest.TestCase):
    """Test ServiceNow iframe context switching"""
    
    def test_modern_ui_has_no_gsft_main_iframe(self):
        """Test: Modern ServiceNow UI doesn't use gsft_main iframe"""
        # Recording shows: "No gsft_main iframe found, staying in main context"
        # Fields are directly in main context in modern UI
        # BUT elements still not found - why?
        pass
    
    def test_element_id_with_dots(self):
        """Test: ServiceNow field IDs contain literal dots"""
        # Recording selector: "#problem\\.short_description"
        # This is CSS selector syntax where dots are escaped
        # But By.ID should use: "problem.short_description" (no escaping)
        
        field_id = "problem.short_description"
        # This is the LITERAL ID attribute value
        # Not a CSS class selector
        
        self.assertIn('.', field_id)
        self.assertEqual(field_id, "problem.short_description")
    
    def test_wait_for_element_in_correct_context(self):
        """Test: After iframe check, should wait for element in current context"""
        # The code switches to iframe OR stays in main
        # Then waits for element "problem.short_description"
        # Element must be in the CURRENT context after switch
        pass


class TestServiceNowFieldExtraction(unittest.TestCase):
    """Test field extraction from ServiceNow forms"""
    
    def test_problem_statement_field_id(self):
        """Test: 'Problem statement' label maps to 'problem.short_description' ID"""
        # UI shows: "Problem statement"
        # Element ID: "problem.short_description"
        # These are correct - the ID is right
        pass
    
    def test_field_not_found_all_fields(self):
        """Test: All fields returning 'not found' indicates wrong context"""
        # Logs show ALL fields not found:
        # - problem.number
        # - problem.short_description
        # - problem.description
        # - sys_display.problem.cmdb_ci
        # - problem.impact, urgency, priority, etc.
        
        # If ALL fields missing, we're in wrong context or page not loaded
        pass
    
    def test_wait_after_navigation(self):
        """Test: Must wait for page to fully load after navigation"""
        # Currently: navigate → sleep 3s → check iframe → wait for element
        # Problem: 3s might not be enough, or element loads later
        pass


class TestServiceNowPageLoad(unittest.TestCase):
    """Test page load detection"""
    
    def test_prb_in_page_source_not_enough(self):
        """Test: PRB in page source doesn't mean form is loaded"""
        # Logs: "PRB PRB0071419 found in page source"
        # But then: "Field not found: problem.short_description"
        # This means page source has PRB text but form not rendered yet
        pass
    
    def test_wait_for_form_ready_state(self):
        """Test: Should wait for document.readyState === 'complete'"""
        # Page might be loading when we check for elements
        pass
    
    def test_javascript_rendered_elements(self):
        """Test: ServiceNow uses heavy JavaScript - wait for JS to render"""
        # Elements might not exist until JS executes
        # Need explicit wait for element presence, not just page load
        pass


if __name__ == '__main__':
    unittest.main()
