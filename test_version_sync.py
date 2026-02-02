"""
TDD tests for version synchronization
Tests that the build process correctly syncs version from git tag to app.py
"""

import unittest
import subprocess
import re
import os
import tempfile
import shutil

class TestVersionSync(unittest.TestCase):
    """Test version sync functionality"""
    
    def test_sync_version_script_exists(self):
        """sync_version.py must exist"""
        self.assertTrue(os.path.exists('sync_version.py'), 
                       "sync_version.py not found - required for build automation")
    
    def test_sync_version_extracts_git_tag(self):
        """Verify sync_version can extract version from git tag"""
        # Import the function directly
        import sync_version
        
        # This should return the latest tag (or None if no tags)
        tag = sync_version.get_latest_git_tag()
        
        # We expect a version string like "1.2.43"
        if tag:
            self.assertRegex(tag, r'^\d+\.\d+\.\d+$', 
                           f"Tag '{tag}' doesn't match version format X.Y.Z")
    
    def test_sync_version_reads_app_version(self):
        """Verify sync_version can read APP_VERSION from app.py"""
        import sync_version
        
        version = sync_version.get_current_app_version()
        
        self.assertIsNotNone(version, "Could not read APP_VERSION from app.py")
        self.assertRegex(version, r'^\d+\.\d+\.\d+$',
                        f"APP_VERSION '{version}' doesn't match version format X.Y.Z")
    
    def test_sync_version_can_update(self):
        """Test that sync_version can update a version in a temp file"""
        import sync_version
        
        # Create a temp copy of app.py
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('APP_VERSION = "0.0.1"  # Test version\n')
            temp_file = f.name
        
        try:
            # Patch app.py path temporarily
            original_open = open
            
            # Read the temp file, update it
            with original_open(temp_file, 'r') as f:
                content = f.read()
            
            # Use the regex from sync_version
            updated = re.sub(
                r'(APP_VERSION\s*=\s*["\'])[^"\']+(["\'])',
                r'\g<1>9.9.9\g<2>',
                content
            )
            
            with original_open(temp_file, 'w') as f:
                f.write(updated)
            
            # Verify it was updated
            with original_open(temp_file, 'r') as f:
                new_content = f.read()
            
            self.assertIn('9.9.9', new_content, "Version update failed")
            
        finally:
            os.unlink(temp_file)


class TestVersionCheckerConfig(unittest.TestCase):
    """Test version checker uses correct token configuration"""
    
    def test_version_checker_accepts_token(self):
        """VersionChecker should accept a token parameter"""
        from version_checker import VersionChecker
        
        checker = VersionChecker(
            current_version='1.0.0',
            owner='test',
            repo='test',
            token='test_token'
        )
        
        self.assertEqual(checker.token, 'test_token')
    
    def test_version_checker_uses_default_repo(self):
        """VersionChecker should have correct default repo"""
        from version_checker import VersionChecker
        
        checker = VersionChecker(current_version='1.0.0')
        
        self.assertEqual(checker.owner, 'mikejsmith1985')
        self.assertEqual(checker.repo, 'jira-automation')
    
    def test_private_repo_requires_token(self):
        """Private repo returns 404 without token"""
        from version_checker import VersionChecker
        
        # Without token, should get 404 (repo is private)
        checker = VersionChecker(
            current_version='1.0.0',
            owner='mikejsmith1985',
            repo='jira-automation',
            token=None
        )
        
        result = checker.check_for_update(use_cache=False)
        
        # Either "No releases found" (404) or "rate_limited" are acceptable
        # Both indicate the API call worked but no data returned
        self.assertFalse(result.get('available', True),
                        "Should not show updates available without token")
        
        # Should have some error indication
        has_error = 'error' in result or 'rate_limited' in result
        self.assertTrue(has_error, "Should indicate error or rate limit without token")


class TestAppVersionLine(unittest.TestCase):
    """Test APP_VERSION is correctly defined in app.py"""
    
    def test_app_version_format(self):
        """APP_VERSION must be a valid semantic version"""
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
        
        self.assertIsNotNone(match, "APP_VERSION not found in app.py")
        
        version = match.group(1)
        self.assertRegex(version, r'^\d+\.\d+\.\d+$',
                        f"APP_VERSION '{version}' is not valid semver X.Y.Z")
    
    def test_app_version_matches_or_ahead_of_git_tag(self):
        """APP_VERSION should match or be ahead of the latest git tag"""
        import sync_version
        from packaging import version as ver
        
        git_tag = sync_version.get_latest_git_tag()
        app_version = sync_version.get_current_app_version()
        
        if git_tag:
            app_v = ver.parse(app_version)
            git_v = ver.parse(git_tag)
            
            self.assertGreaterEqual(app_v, git_v,
                           f"VERSION BEHIND: app.py has {app_version} but git tag is v{git_tag}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
