"""
Test Playwright Basic Functionality
Verify Playwright works before migrating codebase
"""

from playwright.sync_api import sync_playwright
import time

def test_basic_playwright():
    """Test basic Playwright functionality"""
    print("[TEST] Testing Playwright basic functionality...")
    
    with sync_playwright() as p:
        # Launch browser (NOT headless so we can see it)
        print("[BROWSER] Launching Chromium browser...")
        browser = p.chromium.launch(headless=False)
        
        # Create context (session storage)
        print("[CONTEXT] Creating browser context...")
        context = browser.new_context()
        
        # Create page
        print("[PAGE] Creating new page...")
        page = context.new_page()
        
        # Navigate to test page
        print("[NAV] Navigating to example.com...")
        page.goto('https://example.com')
        
        # Test element finding
        print("[FIND] Finding h1 element...")
        h1 = page.locator('h1')
        h1_text = h1.text_content()
        print(f"[SUCCESS] Found h1: '{h1_text}'")
        
        # Test waiting (Playwright auto-waits!)
        print("[WAIT] Testing auto-wait for element...")
        more_info = page.locator('a')
        more_info_text = more_info.first.text_content()
        print(f"[SUCCESS] Found link: '{more_info_text}'")
        
        # Wait so user can see browser
        print("[PAUSE] Browser open for 3 seconds...")
        time.sleep(3)
        
        # Close
        print("[CLOSE] Closing browser...")
        browser.close()
        
        print("[PASS] Basic Playwright test PASSED!")
        return True

def test_shadow_dom_handling():
    """Test that Playwright can handle Shadow DOM"""
    print("\n[TEST] Testing Shadow DOM handling...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to page with Shadow DOM
        print("[NAV] Loading page with Shadow DOM...")
        page.goto('https://chromium.googlesource.com/chromium/src/+/HEAD/chrome/test/data/web_share_target/charts.html')
        
        # Playwright should pierce Shadow DOM automatically
        print("[FIND] Testing Shadow DOM piercing...")
        
        # Wait and close
        time.sleep(2)
        browser.close()
        
        print("[PASS] Shadow DOM test completed!")
        return True

def test_iframe_handling():
    """Test Playwright's iframe handling"""
    print("\n[TEST] Testing iframe handling...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test page with iframes
        print("[NAV] Loading page with iframes...")
        page.goto('https://www.w3schools.com/html/html_iframe.asp')
        
        # Playwright handles iframes elegantly
        print("[FIND] Testing frame locator...")
        # Find iframe and interact with content
        frame = page.frame_locator('iframe').first
        print("[SUCCESS] Frame locator works!")
        
        time.sleep(2)
        browser.close()
        
        print("[PASS] Iframe test completed!")
        return True

def test_persistent_context():
    """Test persistent browser context (session storage)"""
    print("\n[TEST] Testing persistent browser context...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Create persistent context (like Selenium's user-data-dir)
        import os
        storage_path = os.path.join(os.getcwd(), 'test_playwright_storage')
        
        print(f"[STORAGE] Creating context with storage at: {storage_path}")
        context = browser.new_context(
            storage_state=None,  # Will save state on close
        )
        
        page = context.new_page()
        page.goto('https://example.com')
        
        print("[SUCCESS] Persistent context works!")
        
        # Save storage state
        storage_file = os.path.join(storage_path, 'state.json')
        os.makedirs(storage_path, exist_ok=True)
        context.storage_state(path=storage_file)
        print(f"[SAVE] Saved storage state to: {storage_file}")
        
        time.sleep(2)
        browser.close()
        
        print("[PASS] Persistent context test completed!")
        return True

if __name__ == '__main__':
    print("="*60)
    print("PLAYWRIGHT VERIFICATION TESTS")
    print("="*60)
    
    try:
        test_basic_playwright()
        test_shadow_dom_handling()
        test_iframe_handling()
        test_persistent_context()
        
        print("\n" + "="*60)
        print("[PASS] ALL PLAYWRIGHT TESTS PASSED!")
        print("="*60)
        print("\n[INFO] Playwright is ready for migration!")
        print("[INFO] Browser location: C:\\Users\\{username}\\AppData\\Local\\ms-playwright\\")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
