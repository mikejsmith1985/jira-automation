"""
Test script to verify login detection works correctly
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from login_detector import check_login_status

def test_login_detection():
    """Test login detection with a real browser session"""
    print("=== Login Detection Test ===\n")
    
    # Setup Chrome options
    options = Options()
    options.add_argument('--user-data-dir=./selenium_profile')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("[1] Starting Chrome browser with persistent profile...")
    driver = webdriver.Chrome(options=options)
    
    print("[2] Navigating to Jira...")
    driver.get('https://mikejsmith1985.atlassian.net')
    
    print("[3] Waiting 5 seconds for page to load...")
    time.sleep(5)
    
    print("[4] Checking login status...")
    logged_in, user_info = check_login_status(driver)
    
    print(f"\n=== RESULTS ===")
    print(f"Current URL: {driver.current_url}")
    print(f"Logged in: {logged_in}")
    print(f"User info: {user_info}")
    
    if logged_in:
        print("\n✓ SUCCESS: Login detected!")
    else:
        print("\n✗ FAILED: Not logged in or detection failed")
        print("\nPlease log in manually in the browser window, then we'll re-test...")
        input("Press Enter after logging in...")
        
        print("\n[5] Re-checking login status after manual login...")
        logged_in, user_info = check_login_status(driver)
        print(f"Logged in: {logged_in}")
        print(f"User info: {user_info}")
        
        if logged_in:
            print("\n✓ SUCCESS: Login detected after manual login!")
        else:
            print("\n✗ STILL FAILED: Login not detected")
    
    print("\nTest complete. Keeping browser open for 10 seconds...")
    time.sleep(10)
    
    driver.quit()
    print("Browser closed.")

if __name__ == '__main__':
    test_login_detection()
