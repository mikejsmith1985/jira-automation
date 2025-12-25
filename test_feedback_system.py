"""
Unit tests for GitHub Feedback System
Tests the feedback submission and log capture functionality
"""
import unittest
import tempfile
import json
import os
from datetime import datetime, timedelta
from github_feedback import GitHubFeedback, LogCapture


class TestLogCapture(unittest.TestCase):
    """Test log capture functionality"""
    
    def setUp(self):
        """Create temporary log file for testing"""
        self.temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_log.close()
        self.log_capture = LogCapture(self.temp_log.name)
    
    def tearDown(self):
        """Clean up temp file"""
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    def test_add_console_log(self):
        """Test adding console logs"""
        self.log_capture.add_console_log({
            'level': 'error',
            'message': 'Test error message',
            'timestamp': datetime.now().isoformat()
        })
        
        logs = self.log_capture.get_console_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['level'], 'error')
        self.assertIn('Test error message', logs[0]['message'])
    
    def test_add_network_error(self):
        """Test adding network errors"""
        self.log_capture.add_network_error({
            'url': 'https://api.example.com/test',
            'status': 500,
            'error': 'Internal Server Error',
            'timestamp': datetime.now().isoformat()
        })
        
        errors = self.log_capture.get_network_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['status'], 500)
        self.assertIn('api.example.com', errors[0]['url'])
    
    def test_capture_recent_logs(self):
        """Test capturing recent logs from file"""
        # Write test logs
        now = datetime.now()
        with open(self.temp_log.name, 'w') as f:
            for i in range(10):
                timestamp = now - timedelta(minutes=i)
                f.write(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Test log entry {i}\n")
        
        logs = self.log_capture.capture_recent_logs(minutes=5)
        self.assertIsInstance(logs, str)
        self.assertIn('Test log entry', logs)
    
    def test_export_all_logs(self):
        """Test exporting all logs"""
        # Add various log types
        self.log_capture.add_console_log({
            'level': 'error',
            'message': 'Console error',
            'timestamp': datetime.now().isoformat()
        })
        
        self.log_capture.add_network_error({
            'url': 'https://test.com',
            'status': 404,
            'error': 'Not Found',
            'timestamp': datetime.now().isoformat()
        })
        
        export = self.log_capture.export_all_logs()
        
        self.assertIn('## Application Logs', export)
        self.assertIn('## Browser Console Logs', export)
        self.assertIn('## Network Errors', export)
        self.assertIn('Console error', export)
        self.assertIn('Not Found', export)


class TestGitHubFeedback(unittest.TestCase):
    """Test GitHub feedback integration"""
    
    def test_init_without_token(self):
        """Test initialization without token"""
        feedback = GitHubFeedback()
        self.assertIsNone(feedback.token)
        self.assertIsNone(feedback.repo_name)
        self.assertIsNone(feedback.client)
    
    def test_init_with_token(self):
        """Test initialization with token"""
        # Note: This will fail without a real token
        feedback = GitHubFeedback(token='fake_token', repo_name='owner/repo')
        self.assertEqual(feedback.token, 'fake_token')
        self.assertEqual(feedback.repo_name, 'owner/repo')
    
    def test_validate_token_no_token(self):
        """Test token validation without token"""
        feedback = GitHubFeedback()
        result = feedback.validate_token()
        
        self.assertFalse(result['valid'])
        self.assertIsNone(result['user'])
        self.assertIsNotNone(result['error'])
    
    def test_create_issue_structure(self):
        """Test issue creation structure (without actual API call)"""
        feedback = GitHubFeedback()
        
        # Prepare test attachments
        attachments = [
            {
                'name': 'screenshot.png',
                'content': 'base64encodedcontent',
                'mime_type': 'image/png'
            }
        ]
        
        # This will fail without connection, but we test the structure
        result = feedback.create_issue(
            title='Test Issue',
            body='Test description',
            labels=['bug'],
            attachments=attachments
        )
        
        # Should return dict with expected keys
        self.assertIn('success', result)
        self.assertIn('error', result)
        self.assertFalse(result['success'])  # Will fail without real connection


class TestFeedbackIntegration(unittest.TestCase):
    """Integration tests for complete feedback flow"""
    
    def test_complete_feedback_flow(self):
        """Test complete feedback submission flow"""
        # Create log capture
        temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        temp_log.close()
        
        try:
            log_capture = LogCapture(temp_log.name)
            
            # Add test logs
            log_capture.add_console_log({
                'level': 'error',
                'message': 'Test error',
                'timestamp': datetime.now().isoformat()
            })
            
            # Export logs
            logs_export = log_capture.export_all_logs()
            
            # Verify export structure
            self.assertIn('## Application Logs', logs_export)
            self.assertIn('## Browser Console Logs', logs_export)
            
            # Create feedback object (without real token)
            feedback = GitHubFeedback()
            
            # Prepare issue body
            body = "Test feedback\n\n" + logs_export
            
            # Verify body structure
            self.assertIn('Test feedback', body)
            self.assertIn('Test error', body)
            
        finally:
            if os.path.exists(temp_log.name):
                os.unlink(temp_log.name)


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLogCapture))
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubFeedback))
    suite.addTests(loader.loadTestsFromTestCase(TestFeedbackIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("GitHub Feedback System - Unit Tests")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 70)
