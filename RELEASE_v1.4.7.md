# Release v1.4.7 - SAML Redirect Fix

## Summary
Fixed GitHub issue #40: SAML/SSO redirect causes "PRB not found" error even though user is authenticated.

## Problem
User reported error when validating PRB with SAML authentication:
```
[SNOW] Navigating to PRB: https://cigna.service-now.com/problem.do?sysparm_query=number=PRB0071101
[SNOW] Page loaded, checking for PRB...
[SNOW] PRB PRB0071101 not found in page source - wrong page?
```

Form was loading (indicating user was authenticated), but PRB validation failed.

## Root Cause Analysis

### SAML Authentication Flow
1. App navigates to PRB URL
2. ServiceNow detects no SAML session
3. Redirects to IdP (Okta, Azure AD, etc.)
4. User authenticates (or session reused)
5. **SAML redirects back to ServiceNow homepage** (not the PRB page!)
6. App checks for PRB number - not found (wrong page)

### Why Original Code Failed
```python
# Old code
self.page.goto(prb_url, wait_until='networkidle')
page_content = self.page.content()
if prb_number not in page_content:
    return False  # FAILED - we're on homepage!
```

The code assumed `goto()` would land on the requested page. But SAML authentication redirects lose the target URL.

## Solution

### 1. Enhanced SAML Detection
Improved `login_check()` to detect more auth scenarios:

**Before:**
```python
if 'login' in current_url.lower() and 'service-now.com' in current_url:
    return False
```

**After:**
```python
login_indicators = ['login', 'sso', 'saml', 'oauth', 'auth', 'signin', 'logon']
sso_providers = ['okta.com', 'login.microsoftonline.com', 'adfs', ...]

for indicator in login_indicators:
    if indicator in url_lower:
        self.logger.warning(f"Auth page detected: '{indicator}'")
        return False

for provider in sso_providers:
    if provider in url_lower:
        self.logger.warning(f"SSO provider detected: {provider}")
        return False
```

### 2. SAML Redirect Recovery
Modified `navigate_to_prb()` to retry navigation after SAML:

```python
# Initial navigation (may redirect to SAML)
self.page.goto(prb_url, wait_until='networkidle')

# Check where we landed
final_url = self.page.url

# If not on PRB page, SAML likely redirected to homepage
if 'problem.do' not in final_url and prb_number not in final_url:
    self.logger.warning("SAML redirect detected - landed on homepage")
    self.logger.info("Attempting to navigate to PRB again...")
    
    # Try again - SAML session now exists, should work
    self.page.goto(prb_url, wait_until='networkidle')
    final_url = self.page.url
```

### 3. Better Diagnostics
Enhanced error messages with troubleshooting guidance:

```python
if prb_number not in page_content:
    self.logger.error(f"PRB {prb_number} not found in page source")
    self.logger.error(f"Current URL: {self.page.url}")
    self.logger.error("This usually means:")
    self.logger.error("  1. PRB doesn't exist or is misspelled")
    self.logger.error("  2. SAML/SSO redirected to login or home page")
    self.logger.error("  3. You don't have permission to view this PRB")
```

## How It Works Now

### First Run (SAML Auth Required)
```
1. Navigate to PRB → SAML redirect to IdP
2. User authenticates
3. SAML redirects to homepage
4. App detects: 'problem.do' not in final URL
5. App navigates to PRB again
6. SAML session exists, loads PRB directly ✅
```

### Subsequent Runs (Session Cached)
```
1. Navigate to PRB
2. SAML session found in Playwright storage
3. Loads PRB directly (no redirect) ✅
```

### Session Storage
Playwright stores SAML session in:
```
C:\Users\{user}\AppData\Roaming\Waypoint\playwright_profile\state.json
```

Session persists across app restarts until SAML timeout (usually 8-24 hours).

## Testing Scenarios

### Test Case 1: Fresh SAML Auth
1. Clear Playwright profile
2. Validate PRB
3. SAML redirects to IdP
4. Authenticate
5. App retries → PRB loads

### Test Case 2: Cached SAML Session
1. Validate PRB (session exists)
2. No SAML redirect
3. PRB loads immediately

### Test Case 3: Expired SAML Session
1. Wait for SAML timeout
2. Validate PRB
3. SAML redirects to IdP
4. Re-authenticate
5. App retries → PRB loads

## Files Modified
- `servicenow_scraper.py`
  - Lines 35-70: Enhanced `login_check()` with SAML detection
  - Lines 48-120: Updated `navigate_to_prb()` with retry logic

## Commits
- 0193807: Fix #40: Handle SAML redirect when navigating to PRB
- 6cdf724: Bump version to 1.4.7

## Release
- **Version**: v1.4.7
- **Tag**: v1.4.7
- **Build**: Successful (~1m 50s)
- **Assets**: waypoint.exe, waypoint-portable.zip
- **Release URL**: https://github.com/mikejsmith1985/jira-automation/releases/tag/v1.4.7

## User Instructions

### For Users with SAML/SSO
1. Download waypoint.exe v1.4.7
2. Save to permanent location (Desktop, etc.)
3. Configure ServiceNow URL in Settings
4. Test PRB validation - should work through SAML redirects

### Expected Logs (Success)
```
[SNOW] Navigating to PRB: https://cigna.service-now.com/problem.do?...
[SNOW] Page loaded, final URL: https://cigna.service-now.com/nav_to.do
[SNOW] SAML redirect detected - landed on homepage instead of PRB page
[SNOW] Attempting to navigate to PRB again...
[SNOW] Second attempt - final URL: https://cigna.service-now.com/problem.do?...
[SNOW] PRB PRB0071101 confirmed in page source
```

### If Still Fails
1. Check PRB number is correct
2. Verify permissions to view PRB
3. Try manual navigation in browser first
4. Check diagnostics for final URL
5. Report issue with full logs

## Impact
- **Severity**: High (blocked PRB validation for SAML users)
- **Users Affected**: Anyone using ServiceNow with SAML/SSO
- **Common Providers**: Okta, Azure AD, ADFS, PingIdentity, OneLogin
- **Fix**: Automatic retry after SAML redirect

## Technical Notes

### Why Retry Works
After SAML authentication, Playwright stores session cookies. Second navigation finds valid session and loads PRB directly without redirect.

### Alternative Approaches Considered
1. **Wait for specific URL pattern** - Too brittle, varies by SAML config
2. **Parse SAML RelayState** - Complex, not reliable
3. **Use ServiceNow REST API** - Not available (per project constraints)

**Chosen approach:** Simple retry with URL validation. Robust and works for all SAML providers.

### Known Limitations
- Assumes SAML redirects to homepage (most common)
- If SAML redirects elsewhere, second navigation may still fail
- Max 2 navigation attempts (could be configurable)

## Status
✅ Issue #40 in progress (awaiting user testing)
✅ v1.4.7 released
✅ SAML handling improved
✅ All changes committed and pushed
