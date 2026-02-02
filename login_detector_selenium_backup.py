from selenium.webdriver.common.by import By
import time

def check_login_status(driver, debug=False):
    """
    Check if the user is logged in to Jira by looking for common DOM elements.
    Uses multiple strategies to reliably detect login state.
    Returns a tuple (is_logged_in, user_info, debug_info)
    """
    if driver is None:
        return False, None, "Driver is None"
        
    try:
        # Check if browser is still open
        try:
            current_url = driver.current_url
        except Exception as e:
            return False, None, f"Browser not accessible: {e}"

        debug_info = []
        debug_info.append(f"Current URL: {current_url}")

        # Quick check: if on login page, definitely not logged in
        if '/login' in current_url.lower() or '/auth' in current_url.lower():
            return False, None, "On login/auth page"
        
        # Strategy 1: Check for absence of login form
        # If there's NO login form visible, user is likely logged in
        try:
            login_indicators = driver.find_elements(By.CSS_SELECTOR, 'input[name="username"], input[type="email"][placeholder*="email" i]')
            if login_indicators and any(elem.is_displayed() for elem in login_indicators):
                debug_info.append("Login form detected - not logged in")
                return False, None, "; ".join(debug_info)
        except:
            pass
        
        # Strategy 2: Check page title and body content
        try:
            page_title = driver.title.lower()
            if 'log in' in page_title or 'sign in' in page_title:
                return False, None, f"Login page detected in title: {driver.title}"
        except:
            pass
        
        # Strategy 3: Check for logged-in UI elements
        logged_in = False
        user_info = None
        found_selector = None
        
        logged_in_indicators = [
            # High confidence selectors (unique to logged-in state)
            ('button[aria-label*="Your profile and settings"]', 'profile-settings'),
            ('button[data-testid*="profile"]', 'profile-button'),
            ('[data-testid="atlassian-navigation"]', 'navigation'),
            ('[aria-label="Atlassian Navigation"]', 'atlassian-nav'),
            ('button[aria-label="Create"]', 'create-button'),
            ('#createGlobalItem', 'create-global'),
            
            # Sidebar and navigation
            ('[data-testid="navigation-apps-sidebar-software-header-button"]', 'sidebar'),
            ('#ak-jira-navigation', 'jira-navigation'),
            ('nav[data-testid*="navigation"]', 'nav'),
            
            # User menu and avatar
            ('[data-testid="profile-avatar"]', 'avatar'),
            ('.aui-avatar', 'avatar-legacy'),
            ('button[id*="user"]', 'user-button'),
            
            # App switcher (waffle menu)
            ('button[data-testid="app-switcher-button"]', 'app-switcher'),
            ('button[aria-label*="App" i]', 'app-button'),
            
            # Jira-specific elements that only exist when logged in
            ('[data-component-selector="jira-frontend-app"]', 'jira-app'),
            ('[data-testid="software-board"]', 'board'),
            ('div[data-test-id="software-backlog"]', 'backlog'),
        ]
        
        for selector, indicator_type in logged_in_indicators:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for elem in elements:
                        try:
                            if elem.is_displayed():
                                logged_in = True
                                found_selector = f"{selector} ({indicator_type})"
                                if indicator_type == 'username':
                                    user_info = elem.get_attribute('data-username')
                                break
                        except:
                            continue
                if logged_in:
                    break
            except:
                continue
        
        if logged_in:
            debug_info.append(f"Logged in detected via: {found_selector}")
            if debug:
                return logged_in, user_info, "; ".join(debug_info)
            return logged_in, user_info, None
        
        # Strategy 4: URL-based heuristic
        # If we're on a Jira project/board/issue page, we must be logged in
        if 'atlassian.net' in current_url:
            url_patterns_requiring_login = [
                '/browse/',
                '/projects/',
                '/board/',
                '/secure/Dashboard',
                '/jira/software/projects/',
                '/jira/core/projects/',
                '/jira/your-work',
            ]
            for pattern in url_patterns_requiring_login:
                if pattern in current_url:
                    debug_info.append(f"Logged in detected via URL pattern: {pattern}")
                    if debug:
                        return True, None, "; ".join(debug_info)
                    return True, None, None
        
        # Strategy 5: JavaScript-based check (cookies)
        try:
            cookies = driver.get_cookies()
            jira_cookies = [c for c in cookies if 'atlassian' in c.get('domain', '').lower() or 'jira' in c.get('name', '').lower()]
            if jira_cookies:
                debug_info.append(f"Found {len(jira_cookies)} Jira-related cookies")
                # Check for authentication cookies
                auth_cookies = [c for c in jira_cookies if any(x in c.get('name', '').lower() for x in ['token', 'session', 'auth', 'tenant'])]
                if auth_cookies:
                    debug_info.append(f"Authentication cookies present: {[c['name'] for c in auth_cookies]}")
                    if debug:
                        return True, None, "; ".join(debug_info)
                    return True, None, None
        except:
            pass
        
        debug_info.append("No login indicators found")
        if debug:
            return False, None, "; ".join(debug_info)
        return False, None, None
                
    except Exception as e:
        return False, None, f"Error checking login status: {e}"
