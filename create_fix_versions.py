"""
CLI tool to create Jira fixVersions from a list of dates
Usage: python create_fix_versions.py
"""
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from jira_version_creator import JiraVersionCreator
from login_detector import check_login_status
import time
import sys

def setup_driver():
    """Setup Chrome driver with persistent profile"""
    chrome_options = Options()
    chrome_options.add_argument('--user-data-dir=./selenium_profile')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def main():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup driver
    print("🌐 Starting browser...")
    driver = setup_driver()
    
    try:
        # Navigate to Jira
        jira_url = config['jira']['base_url']
        print(f"🔗 Opening Jira: {jira_url}")
        driver.get(jira_url)
        time.sleep(3)
        
        # Check if logged in
        is_logged_in, user_info, debug_info = check_login_status(driver, debug=True)
        
        if not is_logged_in:
            print("\n❌ Not logged in to Jira.")
            print("📋 Please login manually in the browser window...")
            print("⏳ Waiting for you to login (checking every 5 seconds)...\n")
            
            # Wait for manual login
            while not is_logged_in:
                time.sleep(5)
                is_logged_in, user_info, debug_info = check_login_status(driver, debug=False)
            
            print("✅ Login detected!\n")
        else:
            print(f"✅ Already logged in to Jira")
            if debug_info:
                print(f"   {debug_info}\n")
        
        # Get project key
        project_key = config['jira']['project_keys'][0] if config['jira']['project_keys'] else None
        if not project_key:
            print("❌ No project key found in config.yaml")
            print("Please add a project key under jira.project_keys")
            return
        
        print(f"🎯 Target project: {project_key}\n")
        
        # Example 1: Simple weekly sprints
        print("=" * 60)
        print("EXAMPLE 1: Weekly Sprint Releases")
        print("=" * 60)
        
        sprint_dates = [
            '2026-02-05',
            '2026-02-12',
            '2026-02-19',
            '2026-02-26',
            '2026-03-05',
            '2026-03-12'
        ]
        
        print(f"Creating {len(sprint_dates)} sprint versions...")
        print(f"Format: 'Sprint {month_short} {day}'\n")
        
        creator = JiraVersionCreator(driver, config)
        results = creator.create_versions_from_dates(
            dates=sprint_dates,
            name_format='Sprint {month_short} {day}',
            project_key=project_key,
            description_template='Sprint ending on {date}'
        )
        
        # Example 2: Version numbers
        print("\n" + "=" * 60)
        print("EXAMPLE 2: Semantic Version Numbers")
        print("=" * 60)
        
        # Uncomment to try different format:
        # release_dates = [
        #     '2026-03-01',
        #     '2026-04-01',
        #     '2026-05-01'
        # ]
        # 
        # print(f"Creating {len(release_dates)} version releases...")
        # print(f"Format: 'v{year}.{month}.{day}'\n")
        # 
        # results2 = creator.create_versions_from_dates(
        #     dates=release_dates,
        #     name_format='v{year}.{month}.{day}',
        #     project_key=project_key,
        #     description_template='Monthly release {date}'
        # )
        
        print("\n✨ All done! Check your Jira project versions.")
        print(f"🔗 View at: {jira_url}/plugins/servlet/project-config/{project_key}/versions")
        
        # Keep browser open for inspection
        print("\n⏳ Browser will stay open for 10 seconds...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║         Jira fixVersion Batch Creator                      ║
║                                                            ║
║  This tool will create multiple fixVersions in Jira       ║
║  based on a list of release dates.                        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    main()
