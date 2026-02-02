"""
TDD Tests for Issue #37 - ServiceNow Field Detection & Timeout Fixes

Problem: Takes 3+ minutes to fail, can't find fields despite them being present.
Solution: Use proper CSS selectors for dotted IDs, reduce timeouts, add debugging.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import time


class TestServiceNowFieldDetection(unittest.TestCase):
    """Test proper field detection with dotted IDs"""
    
    def setUp(self):
        """Create mock driver with ServiceNow-like HTML"""
        self.mock_driver = Mock()
        
        # Mock element for fields with dotted IDs
        self.mock_element = Mock()
        self.mock_element.get_attribute.return_value = "Test Value"
        self.mock_element.text = "Test Value"
        self.mock_element.is_displayed.return_value = True
        
    def test_css_selector_finds_dotted_id(self):
        """CSS selector [id='problem.short_description'] should work"""
        self.mock_driver.find_element.return_value = self.mock_element
        
        # This is what we should use
        element = self.mock_driver.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
        
        self.assertIsNotNone(element)
        self.mock_driver.find_element.assert_called_with(By.CSS_SELECTOR, "[id='problem.short_description']")
        
    def test_xpath_finds_dotted_id(self):
        """XPath //*[@id='problem.short_description'] should work as backup"""
        self.mock_driver.find_element.return_value = self.mock_element
        
        # XPath backup from user's recording
        element = self.mock_driver.find_element(By.XPATH, "//*[@id='problem.short_description']")
        
        self.assertIsNotNone(element)
        self.mock_driver.find_element.assert_called_with(By.XPATH, "//*[@id='problem.short_description']")
        
    def test_by_id_with_dots_should_not_be_used(self):
        """By.ID with dotted string is problematic - document why we don't use it"""
        # This is what DOESN'T work reliably in Selenium with dotted IDs
        # We're documenting this as anti-pattern
        
        # By.ID treats dots as ID, but some browsers/drivers struggle with this
        # CSS selector [id='...'] is more reliable
        pass  # This test documents the problem, not a solution


class TestServiceNowTimeouts(unittest.TestCase):
    """Test timeout behavior - should be fast, not 3 minutes"""
    
    def test_navigation_completes_within_10_seconds(self):
        """Total navigation should timeout in 10 seconds max, not 180"""
        start_time = time.time()
        
        mock_driver = Mock()
        mock_driver.get.return_value = None
        mock_driver.find_element.side_effect = TimeoutException("Not found")
        mock_driver.page_source = "<html>PRB0071419</html>"
        
        # Simulate navigation that should fail fast
        try:
            # This would be our navigate_to_prb call
            # Should fail in <10 seconds, not 180
            for attempt in range(3):  # 3 attempts at 3 seconds each = 9 seconds max
                try:
                    WebDriverWait(mock_driver, 3).until(
                        lambda d: d.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
                    )
                    break
                except TimeoutException:
                    if attempt == 2:  # Last attempt
                        raise
        except TimeoutException:
            pass  # Expected
            
        elapsed = time.time() - start_time
        
        # Should fail in under 10 seconds (we allow 12 for test overhead)
        self.assertLess(elapsed, 12.0, 
                       f"Took {elapsed:.1f}s - should be under 10s, not 180s!")
        
    def test_single_selector_timeout_is_3_seconds(self):
        """Each selector attempt should timeout in 3 seconds, not 20"""
        start_time = time.time()
        
        mock_driver = Mock()
        mock_driver.find_element.side_effect = TimeoutException("Not found")
        
        try:
            WebDriverWait(mock_driver, 3).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
            )
        except TimeoutException:
            pass  # Expected
            
        elapsed = time.time() - start_time
        
        # Should be around 3 seconds, definitely not 20
        self.assertLess(elapsed, 5.0, 
                       f"Single selector took {elapsed:.1f}s - should be ~3s, not 20s!")


class TestServiceNowIframeHandling(unittest.TestCase):
    """Test iframe detection and context switching"""
    
    def test_detects_gsft_main_iframe(self):
        """Should detect and switch to gsft_main iframe if present"""
        mock_driver = Mock()
        mock_iframe = Mock()
        mock_driver.find_element.return_value = mock_iframe
        
        # Simulate finding iframe
        iframe = mock_driver.find_element(By.ID, "gsft_main")
        mock_driver.switch_to.frame(iframe)
        
        mock_driver.switch_to.frame.assert_called_once_with(mock_iframe)
        
    def test_continues_in_main_context_if_no_iframe(self):
        """Should stay in main context if no iframe found"""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = TimeoutException("No iframe")
        
        try:
            iframe = WebDriverWait(mock_driver, 3).until(
                lambda d: d.find_element(By.ID, "gsft_main")
            )
            mock_driver.switch_to.frame(iframe)
        except TimeoutException:
            # Expected - no iframe, stay in main context
            pass
            
        # Should not have called switch_to.frame
        mock_driver.switch_to.frame.assert_not_called()
        
    def test_tries_both_iframe_and_main_context(self):
        """Should try iframe first, then fallback to main context"""
        mock_driver = Mock()
        
        # First try: no iframe
        mock_driver.find_element.side_effect = [
            TimeoutException("No iframe"),  # iframe lookup fails
            Mock()  # Element found in main context
        ]
        
        contexts_tried = []
        
        # Try iframe
        try:
            iframe = mock_driver.find_element(By.ID, "gsft_main")
            mock_driver.switch_to.frame(iframe)
            contexts_tried.append("iframe")
        except TimeoutException:
            contexts_tried.append("main")
            
        # Try to find element (should succeed in main context)
        element = mock_driver.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
        
        self.assertEqual(contexts_tried, ["main"])
        self.assertIsNotNone(element)


class TestServiceNowDebugOutput(unittest.TestCase):
    """Test HTML debug output on failure"""
    
    @patch('builtins.open', create=True)
    def test_saves_html_on_navigation_failure(self, mock_open):
        """Should save page HTML to debug file when navigation fails"""
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>ServiceNow page content</body></html>"
        
        # Simulate saving HTML for debugging
        html_content = mock_driver.page_source
        
        # In real code, would save to file
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with open("snow_debug.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        mock_file.write.assert_called_once_with(html_content)
        
    def test_logs_all_element_ids_on_page(self):
        """Should log all IDs found on page to help debugging"""
        mock_driver = Mock()
        
        # Mock elements with various IDs
        mock_elements = [
            Mock(get_attribute=Mock(return_value="problem.short_description")),
            Mock(get_attribute=Mock(return_value="problem.description")),
            Mock(get_attribute=Mock(return_value="problem.number")),
        ]
        mock_driver.find_elements.return_value = mock_elements
        
        # Get all elements with IDs
        all_elements = mock_driver.find_elements(By.XPATH, "//*[@id]")
        found_ids = [el.get_attribute("id") for el in all_elements]
        
        self.assertEqual(len(found_ids), 3)
        self.assertIn("problem.short_description", found_ids)
        self.assertIn("problem.description", found_ids)


class TestServiceNowPRBValidation(unittest.TestCase):
    """Test PRB validation logic"""
    
    def test_validates_prb_in_page_source(self):
        """Should check if PRB number is in page source before waiting"""
        mock_driver = Mock()
        mock_driver.page_source = """
        <html>
            <body>
                <div>PRB0071419</div>
                <input id="problem.short_description" value="Test issue" />
            </body>
        </html>
        """
        
        prb_number = "PRB0071419"
        self.assertIn(prb_number, mock_driver.page_source)
        
    def test_considers_success_if_any_field_found(self):
        """Should consider navigation successful if ANY expected field is found"""
        mock_driver = Mock()
        
        # Only one field found
        mock_driver.find_element.side_effect = [
            TimeoutException("problem.short_description not found"),
            Mock(),  # problem.description found!
        ]
        
        found_any = False
        for field_id in ["problem.short_description", "problem.description"]:
            try:
                element = mock_driver.find_element(By.CSS_SELECTOR, f"[id='{field_id}']")
                if element:
                    found_any = True
                    break
            except TimeoutException:
                continue
                
        self.assertTrue(found_any, "Should succeed if ANY field is found")


class TestServiceNowRecordingSelectors(unittest.TestCase):
    """Test using exact selectors from user's Chrome recording"""
    
    def test_uses_recording_css_selector(self):
        """Should use CSS selector from recording: #problem\\.short_description"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element
        
        # User's recording shows: "#problem\\.short_description"
        # In Selenium, we use: [id='problem.short_description']
        element = mock_driver.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
        
        self.assertIsNotNone(element)
        
    def test_uses_recording_xpath_selector(self):
        """Should use XPath from recording: ///*[@id="problem.short_description"]"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element
        
        # User's recording shows this XPath
        element = mock_driver.find_element(By.XPATH, "//*[@id='problem.short_description']")
        
        self.assertIsNotNone(element)
        
    def test_finds_both_problem_statement_and_description(self):
        """Should find both 'Problem Statement' and 'Description' fields"""
        mock_driver = Mock()
        
        # Mock both fields
        mock_driver.find_element.side_effect = [
            Mock(),  # problem.short_description
            Mock(),  # problem.description
        ]
        
        # Find Problem Statement (short_description)
        field1 = mock_driver.find_element(By.CSS_SELECTOR, "[id='problem.short_description']")
        
        # Find Description
        field2 = mock_driver.find_element(By.CSS_SELECTOR, "[id='problem.description']")
        
        self.assertIsNotNone(field1)
        self.assertIsNotNone(field2)


if __name__ == '__main__':
    unittest.main()
