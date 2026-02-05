"""Test config save logic to ensure PAT persistence"""
import os
import sys
import yaml
import tempfile

# Simulate the handle_save_integrations logic
def test_save_integrations():
    """Test that partial updates preserve existing config"""
    
    # Setup temp config file
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.yaml')
    
    # Scenario 1: Save feedback token first
    print("=" * 60)
    print("TEST 1: Save feedback token")
    print("=" * 60)
    
    config = {}
    data = {
        'feedback': {
            'github_token': 'ghp_secret123',
            'repo': 'user/repo'
        }
    }
    
    # Apply update logic
    if 'feedback' in data:
        if 'feedback' not in config:
            config['feedback'] = {}
        if 'github_token' in data['feedback']:
            config['feedback']['github_token'] = data['feedback']['github_token']
        if 'repo' in data['feedback']:
            config['feedback']['repo'] = data['feedback']['repo']
    
    # Save
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Saved config: {config}")
    
    # Verify
    with open(config_path, 'r', encoding='utf-8') as f:
        saved = yaml.safe_load(f)
    
    assert saved['feedback']['github_token'] == 'ghp_secret123', "Token not saved!"
    print("✓ Token saved correctly\n")
    
    # Scenario 2: Save GitHub settings (should preserve feedback)
    print("=" * 60)
    print("TEST 2: Save GitHub settings (should preserve feedback)")
    print("=" * 60)
    
    # Load existing config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    print(f"Loaded config: {config}")
    
    # New request - only github section
    data = {
        'github': {
            'api_token': 'ghp_github_token',
            'organization': 'myorg'
        }
    }
    
    # Apply update logic (same as app.py)
    if 'github' in data:
        if 'github' not in config:
            config['github'] = {}
        if 'api_token' in data['github']:
            config['github']['api_token'] = data['github']['api_token']
        if 'organization' in data['github']:
            config['github']['organization'] = data['github']['organization']
    
    # Save
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Saved config: {config}")
    
    # Verify feedback still exists
    with open(config_path, 'r', encoding='utf-8') as f:
        saved = yaml.safe_load(f)
    
    print(f"Final config: {saved}")
    
    assert 'feedback' in saved, "❌ FAIL: Feedback section deleted!"
    assert saved['feedback']['github_token'] == 'ghp_secret123', "❌ FAIL: Token lost!"
    assert saved['github']['organization'] == 'myorg', "❌ FAIL: GitHub settings not saved!"
    
    print("✓ Feedback token preserved after GitHub save!")
    print("✓ All sections coexist correctly!")
    
    # Cleanup
    os.remove(config_path)
    os.rmdir(temp_dir)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_save_integrations()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
