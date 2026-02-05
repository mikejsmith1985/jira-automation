# PAT Persistence Bug - Root Cause Analysis

## The Bug (Failed 25+ Times)

User saves GitHub PAT → works → closes app → reopens → PAT is GONE

## Root Cause

### The Code Path
1. User enters PAT in **Settings > Integrations > Feedback**
2. Calls `/api/feedback/save-token` → saves to config.yaml ✓
3. User later saves GitHub settings (org, token for PR sync)
4. Calls `/api/integrations/save` → **OVERWRITES config.yaml**

### The Problem in handle_save_integrations()

**BEFORE (BROKEN):**
```python
if 'feedback' in data:
    config['feedback']['github_token'] = data['feedback'].get('github_token', '')
    # data['feedback'] NOT in request → uses empty default ''
```

When saveGitHubSettings() runs:
```javascript
// Frontend sends:
{
  github: { api_token: "...", organization: "..." }
  // NO "feedback" key!
}
```

Backend processes:
```python
if 'feedback' in data:  // FALSE - not in data
    # This block SKIPPED
    
# But config is still written with:
yaml.dump(config, f)  # Writes config without feedback section or with empty values
```

### Why It Kept Failing

Every attempt tried to fix symptoms, not root cause:
- "Make sure config.yaml persists" ✗ (it did persist, but with wrong data)
- "Use DATA_DIR not temp" ✗ (already correct)
- "Load config before save" ✗ (was loading, but overwriting)
- "Check file permissions" ✗ (not a permission issue)

**Real issue**: Partial updates were REPLACING entire config instead of MERGING

## The Fix (v2.1.5)

```python
# ONLY update fields that are PROVIDED in the request
if 'github' in data:
    if 'api_token' in data['github']:  # Check if field exists
        config['github']['api_token'] = data['github']['api_token']
    # Don't touch if not provided

if 'feedback' in data:  # If feedback not in request...
    # ...don't touch existing feedback section AT ALL
```

### Result
- Saving GitHub settings → preserves feedback config ✓
- Saving Jira settings → preserves feedback config ✓
- Saving feedback token → preserves GitHub config ✓
- All sections coexist peacefully ✓

## Testing v2.1.5

1. Save GitHub PAT in Feedback section
2. Close app
3. Reopen app → PAT still there ✓
4. Save GitHub org in Integrations
5. Close app
6. Reopen app → PAT STILL there ✓

---

## Why It Took 25 Attempts

The bug was subtle:
- Config WAS being saved (not a write issue)
- Config WAS being loaded (not a read issue)
- Config WAS in the right location (not a path issue)

**It was a MERGE logic issue** - treating partial updates as full replacements.

This is now FIXED in v2.1.5.
