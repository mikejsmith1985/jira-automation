# FINAL FIX - Update Checker Uses Same Token as Feedback

## The Problem You Identified

> "Why is this not working off of the same PAT I use for feedback? That's how it should be setup."

You were absolutely right. The update checker was:
1. Using its own hardcoded owner/repo
2. Trying to use a separate GitHub token
3. Not leveraging the feedback system config

## What I Fixed

### Before ❌
```python
# Hardcoded owner/repo
checker = VersionChecker(
    current_version=APP_VERSION,
    owner='mikejsmith1985',  # HARDCODED!
    repo='jira-automation',   # HARDCODED!
    token=github_token  # Different token path
)
```

### After ✅
```python
# Read from feedback config
github_token = cfg.get('feedback', {}).get('github_token')

# Parse repo from feedback.repo (format: "owner/repo")
feedback_repo = cfg.get('feedback', {}).get('repo', '')
if feedback_repo and '/' in feedback_repo:
    repo_owner, repo_name = feedback_repo.split('/', 1)

checker = VersionChecker(
    current_version=APP_VERSION,
    owner=repo_owner,  # From feedback.repo
    repo=repo_name,    # From feedback.repo
    token=github_token  # From feedback.github_token
)
```

## How It Works Now

### One Token, Two Features

**Config (config.yaml):**
```yaml
feedback:
  github_token: ghp_your_token_here
  repo: mikejsmith1985/jira-automation
```

**What Gets Used:**
1. **Feedback System** → Uses `feedback.github_token` + `feedback.repo`
2. **Update Checker** → Uses `feedback.github_token` + `feedback.repo`
3. **Same PAT for both!** ✅

### User Experience

**Setup (One Time):**
1. Go to Settings → Feedback
2. Enter GitHub PAT
3. Enter repo (format: `owner/repo`)
4. Save

**Both Features Work:**
- 🐛 **Bug button** → Submits to your feedback repo
- 🔄 **Update checker** → Checks releases in same repo
- **One token, two features!**

### Repo Flexibility

If your feedback repo is DIFFERENT from your releases repo:
```yaml
# Example: Feedback goes to fork, releases from main
feedback:
  github_token: ghp_token
  repo: yourfork/jira-automation  # Your fork for issues

# Update checker will look here for releases:
# But you're saying they're the SAME repo, so no conflict!
```

## Technical Implementation

### Code Location: app.py lines 800-848

```python
def _handle_check_updates(self):
    """Check for available updates"""
    # Get token from feedback config
    github_token = cfg.get('feedback', {}).get('github_token')
    
    # Parse owner/repo from feedback.repo
    feedback_repo = cfg.get('feedback', {}).get('repo', '')
    if feedback_repo and '/' in feedback_repo:
        repo_owner, repo_name = feedback_repo.split('/', 1)
        safe_print(f"[UPDATE] Using repo from feedback config: {repo_owner}/{repo_name}")
    
    # Fallback: Try github.api_token if feedback not set
    if not github_token:
        github_token = cfg.get('github', {}).get('api_token')
    
    # Create checker with feedback config
    checker = VersionChecker(
        current_version=APP_VERSION,
        owner=repo_owner,
        repo=repo_name,
        token=github_token
    )
```

### Logging

When update checker runs, you'll see in console:
```
[UPDATE] Using repo from feedback config: mikejsmith1985/jira-automation
```

This confirms it's using the feedback config.

## Testing

### Manual Test
1. Open app
2. Check console/logs
3. Click "Check for Updates"
4. Should see: `[UPDATE] Using repo from feedback config: owner/repo`
5. Should work if feedback token is valid

### Verify Token is Used
```python
# Check config
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
    
print("Feedback token:", cfg['feedback']['github_token'][:10] + "...")
print("Feedback repo:", cfg['feedback']['repo'])

# Both feedback and updates use these same values
```

## Benefits

### Single Source of Truth
- One place to configure GitHub access
- One token to manage
- One repo setting

### Consistency
- Feedback submissions go to correct repo
- Release checks come from correct repo
- No confusion about where issues/releases are

### User-Friendly
- User only needs to set up feedback once
- Update checker automatically works
- No duplicate configuration

## Summary

**You were right** - the update checker should use the same PAT as feedback. 

**Now it does:**
- ✅ Uses `feedback.github_token`
- ✅ Uses `feedback.repo` to determine owner/repo
- ✅ Same token for both features
- ✅ No hardcoded values
- ✅ Works with any repo format

**Build:** waypoint.exe ready in dist/  
**Version:** 1.2.43  
**Status:** Ready to test with your feedback token

The update checker will now automatically use your existing feedback configuration!
