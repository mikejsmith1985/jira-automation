"""
TDD Tests for GitHub PAT Persistence Bug (Issue: PAT lost after restart)

The bug: User saves PAT in feedback config, restarts app, PAT is GONE but UI shows "configured"
This means the PAT is being lost during save/load cycle.

These tests MUST fail first to expose the bug, then pass after fix.
"""

import unittest
import os
import tempfile
import shutil
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.config_manager import ConfigManager


class TestPATPersistence(unittest.TestCase):
    """Test that GitHub PAT actually persists across config manager instances"""
    
    def setUp(self):
        """Create temporary directory for test configs"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
        
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_pat_persists_after_save_and_reload(self):
        """CRITICAL: PAT must persist when config is saved and reloaded"""
        test_token = 'ghp_test1234567890abcdefghijklmnopqr'
        
        # Step 1: Create config manager and save PAT
        cm1 = ConfigManager(self.config_path)
        cm1.set('feedback.github_token', test_token)
        cm1.set('feedback.repo', 'mikejsmith1985/jira-automation')
        success = cm1.save()
        
        self.assertTrue(success, "Save should succeed")
        
        # Step 2: Create NEW config manager (simulates app restart)
        cm2 = ConfigManager(self.config_path)
        
        # Step 3: Verify PAT is still there
        loaded_token = cm2.get('feedback.github_token')
        
        self.assertEqual(loaded_token, test_token, 
                        f"PAT should persist! Got: {loaded_token}, Expected: {test_token}")
    
    def test_pat_in_yaml_file_after_save(self):
        """Verify PAT is actually written to YAML file"""
        test_token = 'ghp_test_token_should_be_in_file'
        
        # Save config with PAT
        cm = ConfigManager(self.config_path)
        cm.set('feedback.github_token', test_token)
        cm.save()
        
        # Read raw YAML file
        with open(self.config_path, 'r') as f:
            raw_yaml = yaml.safe_load(f)
        
        # Check if PAT is in file
        self.assertIn('feedback', raw_yaml, "feedback section should exist in YAML")
        self.assertIn('github_token', raw_yaml['feedback'], "github_token should exist in feedback")
        self.assertEqual(raw_yaml['feedback']['github_token'], test_token,
                        "PAT in YAML file should match what we saved")
    
    def test_multiple_save_load_cycles_preserve_pat(self):
        """PAT should survive multiple save/load cycles"""
        test_token = 'ghp_persistent_token_123'
        
        # Cycle 1: Save
        cm1 = ConfigManager(self.config_path)
        cm1.set('feedback.github_token', test_token)
        cm1.save()
        
        # Cycle 2: Load and save again
        cm2 = ConfigManager(self.config_path)
        self.assertEqual(cm2.get('feedback.github_token'), test_token)
        cm2.set('jira.base_url', 'https://test.atlassian.net')  # Change something else
        cm2.save()
        
        # Cycle 3: Load again
        cm3 = ConfigManager(self.config_path)
        self.assertEqual(cm3.get('feedback.github_token'), test_token,
                        "PAT should survive multiple save/load cycles")
    
    def test_defaults_dont_overwrite_pat(self):
        """DEFAULT_CONFIG merge should not wipe out saved PAT"""
        test_token = 'ghp_should_not_be_overwritten'
        
        # Save PAT
        cm1 = ConfigManager(self.config_path)
        cm1.set('feedback.github_token', test_token)
        cm1.save()
        
        # Load with defaults applied (this is where bug might be)
        cm2 = ConfigManager(self.config_path)
        cm2._apply_defaults()  # Explicitly call to test
        
        loaded_token = cm2.get('feedback.github_token')
        self.assertEqual(loaded_token, test_token,
                        "Applying defaults should NOT wipe out PAT")
    
    def test_empty_feedback_section_gets_created(self):
        """If feedback section doesn't exist, it should be created (not cause errors)"""
        cm = ConfigManager(self.config_path)
        
        # Set PAT when feedback section doesn't exist yet
        cm.set('feedback.github_token', 'ghp_new_token')
        cm.save()
        
        # Reload and verify
        cm2 = ConfigManager(self.config_path)
        self.assertEqual(cm2.get('feedback.github_token'), 'ghp_new_token')
    
    def test_feedback_section_has_defaults(self):
        """Feedback section should have proper defaults in DEFAULT_CONFIG"""
        cm = ConfigManager(self.config_path)
        
        # Check if feedback section exists in defaults
        self.assertIn('feedback', cm.DEFAULT_CONFIG, 
                     "feedback should be in DEFAULT_CONFIG")
        
        # Check if github_token key exists
        self.assertIn('github_token', cm.DEFAULT_CONFIG['feedback'],
                     "github_token should be in DEFAULT_CONFIG['feedback']")
    
    def test_pat_not_lost_when_other_config_saved(self):
        """Saving other config sections should NOT erase PAT"""
        test_token = 'ghp_should_remain_after_other_saves'
        
        cm = ConfigManager(self.config_path)
        cm.set('feedback.github_token', test_token)
        cm.save()
        
        # Modify other sections
        cm.set('jira.base_url', 'https://jira.example.com')
        cm.set('github.organization', 'myorg')
        cm.save()
        
        # Verify PAT still there
        self.assertEqual(cm.get('feedback.github_token'), test_token,
                        "PAT should not be lost when saving other config")
    
    def test_config_shows_configured_matches_actual_token(self):
        """UI shows 'configured' should match whether token actually exists"""
        test_token = 'ghp_real_token'
        
        cm = ConfigManager(self.config_path)
        cm.set('feedback.github_token', test_token)
        cm.save()
        
        # Reload
        cm2 = ConfigManager(self.config_path)
        loaded_token = cm2.get('feedback.github_token')
        
        # Check if token would show as "configured" in UI logic
        is_configured = bool(loaded_token and 
                           loaded_token != '' and 
                           loaded_token != 'YOUR_GITHUB_TOKEN_HERE')
        
        self.assertTrue(is_configured, 
                       "Token should show as configured when it exists")
        self.assertEqual(loaded_token, test_token,
                       "Actual token should match when showing configured")


class TestConfigManagerFeedbackSection(unittest.TestCase):
    """Test config_manager specifically handles feedback section correctly"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_feedback_section_in_default_config(self):
        """DEFAULT_CONFIG must include feedback section"""
        cm = ConfigManager(self.config_path)
        
        self.assertIn('feedback', cm.DEFAULT_CONFIG,
                     "DEFAULT_CONFIG missing 'feedback' section!")
        self.assertIsInstance(cm.DEFAULT_CONFIG['feedback'], dict,
                            "feedback should be a dict")
    
    def test_feedback_defaults_have_all_fields(self):
        """Feedback defaults should have github_token and repo"""
        cm = ConfigManager(self.config_path)
        feedback_defaults = cm.DEFAULT_CONFIG.get('feedback', {})
        
        self.assertIn('github_token', feedback_defaults,
                     "feedback defaults missing github_token")
        self.assertIn('repo', feedback_defaults,
                     "feedback defaults missing repo")
    
    def test_merge_preserves_existing_feedback_values(self):
        """_merge_defaults should preserve existing feedback values"""
        cm = ConfigManager(self.config_path)
        
        # Manually create config with feedback
        existing_config = {
            'feedback': {
                'github_token': 'ghp_existing_token',
                'repo': 'user/repo'
            }
        }
        
        # Merge with defaults
        merged = cm._merge_defaults(cm.DEFAULT_CONFIG, existing_config)
        
        # Check if existing values preserved
        self.assertEqual(merged['feedback']['github_token'], 'ghp_existing_token',
                        "_merge_defaults overwrote existing token!")
        self.assertEqual(merged['feedback']['repo'], 'user/repo',
                        "_merge_defaults overwrote existing repo!")


class TestPATRealWorldScenario(unittest.TestCase):
    """Test real-world scenario: User saves PAT, closes app, reopens"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_user_saves_pat_and_restarts_app(self):
        """
        Real scenario:
        1. User enters PAT in UI
        2. Backend saves to config
        3. User closes app
        4. User reopens app
        5. PAT should still be there
        """
        user_token = 'ghp_user_entered_this_token_123'
        
        # === USER SESSION 1: Save PAT ===
        session1_cm = ConfigManager(self.config_path)
        session1_cm.set('feedback.github_token', user_token)
        session1_cm.set('feedback.repo', 'mikejsmith1985/jira-automation')
        save_success = session1_cm.save()
        self.assertTrue(save_success, "User's save failed!")
        
        # App closes (config manager destroyed)
        del session1_cm
        
        # === USER SESSION 2: Reopen app ===
        session2_cm = ConfigManager(self.config_path)
        
        # Check if PAT is still there
        loaded_token = session2_cm.get('feedback.github_token')
        loaded_repo = session2_cm.get('feedback.repo')
        
        self.assertEqual(loaded_token, user_token,
                        f"USER'S PAT WAS LOST! Expected: {user_token}, Got: {loaded_token}")
        self.assertEqual(loaded_repo, 'mikejsmith1985/jira-automation',
                        "User's repo was lost!")
        
        # Verify UI would show "configured"
        is_configured = bool(loaded_token and 
                           loaded_token not in ['', 'YOUR_GITHUB_TOKEN_HERE'])
        self.assertTrue(is_configured, 
                       "UI should show 'configured' but token is missing!")


if __name__ == '__main__':
    unittest.main(verbosity=2)
