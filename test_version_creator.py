"""
Test the fixVersion creator module
"""
import unittest
from datetime import datetime
from jira_version_creator import JiraVersionCreator

class MockDriver:
    """Mock Selenium driver for testing"""
    def __init__(self):
        self.current_url = "https://test.atlassian.net/browse/TEST-1"
        self.title = "Test Issue"
        self.cookies = []
    
    def get(self, url):
        self.current_url = url
    
    def find_element(self, by, value):
        pass
    
    def find_elements(self, by, value):
        return []
    
    def get_cookies(self):
        return self.cookies

class TestJiraVersionCreator(unittest.TestCase):
    """Test fixVersion creation logic"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.config = {
            'jira': {
                'base_url': 'https://test.atlassian.net',
                'project_keys': ['TEST', 'DEMO']
            }
        }
        self.driver = MockDriver()
        self.creator = JiraVersionCreator(self.driver, self.config)
    
    def test_format_version_name_simple_date(self):
        """Test simple date formatting"""
        date_obj = datetime(2026, 2, 5)
        result = self.creator._format_version_name('Release {date}', date_obj)
        self.assertEqual(result, 'Release 2026-02-05')
    
    def test_format_version_name_semantic_version(self):
        """Test semantic version format"""
        date_obj = datetime(2026, 3, 15)
        result = self.creator._format_version_name('v{year}.{month}.{day}', date_obj)
        self.assertEqual(result, 'v2026.03.15')
    
    def test_format_version_name_sprint_style(self):
        """Test sprint-style naming"""
        date_obj = datetime(2026, 2, 5)
        result = self.creator._format_version_name('Sprint {month_short} {day}', date_obj)
        self.assertEqual(result, 'Sprint Feb 05')
    
    def test_format_version_name_full_month(self):
        """Test full month name"""
        date_obj = datetime(2026, 12, 25)
        result = self.creator._format_version_name('{month_name} {day} Release', date_obj)
        self.assertEqual(result, 'December 25 Release')
    
    def test_format_version_name_year_only(self):
        """Test year-only format"""
        date_obj = datetime(2026, 1, 1)
        result = self.creator._format_version_name('Release {year}', date_obj)
        self.assertEqual(result, 'Release 2026')
    
    def test_format_version_name_complex(self):
        """Test complex format with multiple placeholders"""
        date_obj = datetime(2026, 6, 15)
        result = self.creator._format_version_name(
            'v{year}.{month}-{day} ({month_name})', 
            date_obj
        )
        self.assertEqual(result, 'v2026.06-15 (June)')
    
    def test_config_initialization(self):
        """Test that creator initializes with config"""
        self.assertEqual(self.creator.base_url, 'https://test.atlassian.net')
        self.assertEqual(self.creator.config['jira']['project_keys'][0], 'TEST')
    
    def test_date_parsing_valid(self):
        """Test that valid dates are parsed correctly"""
        test_dates = ['2026-01-01', '2026-12-31', '2026-02-29']  # 2026 is not a leap year
        
        for date_str in test_dates[:2]:  # Skip leap year for now
            try:
                parsed = datetime.strptime(date_str, '%Y-%m-%d')
                self.assertIsInstance(parsed, datetime)
            except ValueError:
                self.fail(f"Failed to parse valid date: {date_str}")
    
    def test_date_parsing_invalid(self):
        """Test that invalid dates raise errors"""
        invalid_dates = ['2026-13-01', '2026-00-01', '2026-01-32', 'not-a-date']
        
        for date_str in invalid_dates:
            with self.assertRaises(ValueError):
                datetime.strptime(date_str, '%Y-%m-%d')

class TestVersionNameFormats(unittest.TestCase):
    """Test various version naming strategies"""
    
    def setUp(self):
        self.config = {
            'jira': {
                'base_url': 'https://test.atlassian.net',
                'project_keys': ['TEST']
            }
        }
        self.creator = JiraVersionCreator(MockDriver(), self.config)
    
    def test_format_options(self):
        """Test all documented format options"""
        date_obj = datetime(2026, 3, 15)
        
        formats = {
            'Release {date}': 'Release 2026-03-15',
            'v{year}.{month}.{day}': 'v2026.03.15',
            'Sprint {month_short} {day}': 'Sprint Mar 15',
            '{month_name} {day}, {year} Release': 'March 15, 2026 Release',
            '{year}.{month}': '2026.03',
        }
        
        for format_str, expected in formats.items():
            with self.subTest(format=format_str):
                result = self.creator._format_version_name(format_str, date_obj)
                self.assertEqual(result, expected)

def run_tests():
    """Run all tests"""
    print("🧪 Running fixVersion creator tests...\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestJiraVersionCreator))
    suite.addTests(loader.loadTestsFromTestCase(TestVersionNameFormats))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} test(s) had errors")
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
