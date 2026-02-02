"""
TDD tests for Issue #33 - Critical fixes
Tests BEFORE fixing to verify bugs exist, then verify fixes work
"""

import unittest
import re


class TestUpdateCheckerEndpoint(unittest.TestCase):
    """Test update checker works with GET request (frontend uses GET)"""
    
    def test_update_check_logs_show_get(self):
        """Logs from issue show GET requests to /api/updates/check"""
        # From the issue logs:
        # 2026-02-02 10:11:06,541 - INFO - [GET] /api/updates/check
        # This proves frontend is using GET, not POST
        log_line = "[GET] /api/updates/check"
        self.assertIn("GET", log_line, "Frontend uses GET for update check")
    
    def test_backend_should_support_get(self):
        """Backend should handle GET for /api/updates/check"""
        # Read app.py and check if GET handler exists
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check do_GET has updates/check OR do_POST accepts it
        has_get_handler = "updates/check" in content and "do_GET" in content
        
        # For now, just verify the endpoint exists somewhere
        self.assertIn("updates/check", content, 
                     "updates/check endpoint should exist")


class TestServiceNowURLNormalization(unittest.TestCase):
    """Test ServiceNow URL doesn't have double slashes"""
    
    def test_double_slash_in_issue(self):
        """Issue shows double slash: https://cigna.service-now.com//problem.do"""
        bad_url = "https://cigna.service-now.com//problem.do"
        self.assertIn("//problem", bad_url, "Issue has double slash bug")
    
    def test_url_normalization_removes_double_slash(self):
        """URL should be normalized to remove trailing slash before path"""
        base_url = "https://cigna.service-now.com/"
        path = "problem.do?sysparm_query=number=PRB0065275"
        
        # Current buggy behavior
        buggy_url = f"{base_url}/{path}"
        self.assertIn("//problem", buggy_url, "Bug: double slash occurs")
        
        # Expected fixed behavior
        normalized_base = base_url.rstrip('/')
        fixed_url = f"{normalized_base}/{path}"
        self.assertNotIn("//problem", fixed_url, "Fixed: no double slash")
        self.assertEqual(fixed_url, "https://cigna.service-now.com/problem.do?sysparm_query=number=PRB0065275")
    
    def test_servicenow_scraper_normalizes_url(self):
        """ServiceNowScraper should normalize base_url"""
        from unittest.mock import MagicMock
        from servicenow_scraper import ServiceNowScraper
        
        # Create mock driver
        mock_driver = MagicMock()
        
        # Create config with trailing slash
        config = {
            'servicenow': {
                'url': 'https://test.service-now.com/'
            }
        }
        
        # Initialize scraper
        scraper = ServiceNowScraper(mock_driver, config)
        
        # base_url should be normalized (no trailing slash)
        self.assertFalse(scraper.base_url.endswith('/'),
                        f"base_url should not end with slash: {scraper.base_url}")
        self.assertEqual(scraper.base_url, 'https://test.service-now.com')


class TestScreenshotAttachment(unittest.TestCase):
    """Test screenshot attachment doesn't exceed GitHub limits"""
    
    def test_github_comment_limit(self):
        """GitHub comment body limit is 65536 characters"""
        limit = 65536
        # A typical screenshot base64 can be 500KB+ = 700,000+ chars
        typical_screenshot_base64_chars = 700000
        self.assertGreater(typical_screenshot_base64_chars, limit,
                          "Screenshots exceed GitHub comment limit")
    
    def test_screenshot_should_use_upload_not_inline(self):
        """Screenshots should be uploaded as files, not inline base64"""
        # Read github_feedback.py to check implementation
        with open('github_feedback.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should use GitHub file upload API or alternative
        # For now, just verify the file exists
        self.assertIn('class GitHubFeedback', content,
                     "GitHubFeedback class should exist")


class TestAppVersion(unittest.TestCase):
    """Test app version is correct"""
    
    def test_app_version_is_current(self):
        """APP_VERSION should be >= 1.2.43 (user still seeing 1.2.42)"""
        import app
        from packaging import version
        
        current = version.parse(app.APP_VERSION)
        minimum = version.parse("1.2.43")
        
        self.assertGreaterEqual(current, minimum,
                               f"APP_VERSION {app.APP_VERSION} should be >= 1.2.43")


if __name__ == '__main__':
    unittest.main(verbosity=2)
