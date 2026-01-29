"""
Jira fixVersion Creator
Creates fixVersions in Jira using browser automation
"""
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from login_detector import check_login_status

class JiraVersionCreator:
    """Creates fixVersions in Jira via Selenium"""
    
    def __init__(self, driver, config):
        """
        Initialize the version creator
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary with jira.base_url and jira.project_keys
        """
        self.driver = driver
        self.config = config
        self.base_url = config['jira']['base_url']
        
    def create_versions_from_dates(self, dates, name_format, project_key=None, description_template="", archive_old=False):
        """
        Create multiple fixVersions from a list of dates
        
        Args:
            dates: List of date strings (e.g., ['2026-02-05', '2026-02-12'])
            name_format: Format string for version name (e.g., 'Release {date}' or 'v{year}.{month}.{day}')
            project_key: Jira project key (e.g., 'KAN'). If None, uses first from config
            description_template: Optional description template (e.g., 'Sprint ending {date}')
            archive_old: Whether to archive versions after their release date
            
        Returns:
            Dictionary with results:
            {
                'created': [list of created versions],
                'failed': [list of failed versions with errors],
                'skipped': [list of already existing versions]
            }
        """
        # Use first project from config if not specified
        if project_key is None:
            project_key = self.config['jira']['project_keys'][0]
        
        # Verify login
        is_logged_in, _, _ = check_login_status(self.driver)
        if not is_logged_in:
            print("❌ Not logged in to Jira. Please login first.")
            return {'created': [], 'failed': [], 'skipped': []}
        
        results = {
            'created': [],
            'failed': [],
            'skipped': []
        }
        
        print(f"🚀 Creating {len(dates)} fixVersions for project {project_key}...")
        
        for date_str in dates:
            try:
                # Parse the date
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    print(f"⚠️ Invalid date format '{date_str}' (expected YYYY-MM-DD), skipping...")
                    results['failed'].append({'date': date_str, 'error': 'Invalid date format'})
                    continue
                
                # Format the version name
                version_name = self._format_version_name(name_format, date_obj)
                
                # Format description if template provided
                description = ""
                if description_template:
                    description = description_template.replace('{date}', date_str)
                
                # Create the version
                success = self.create_version(
                    project_key=project_key,
                    version_name=version_name,
                    release_date=date_str,
                    description=description,
                    archived=archive_old and date_obj < datetime.now()
                )
                
                if success:
                    print(f"  ✅ Created version: {version_name}")
                    results['created'].append(version_name)
                else:
                    print(f"  ⚠️ Skipped (may already exist): {version_name}")
                    results['skipped'].append(version_name)
                
                # Small delay between creations
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error creating version for {date_str}: {e}")
                results['failed'].append({'date': date_str, 'error': str(e)})
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  ✅ Created: {len(results['created'])}")
        print(f"  ⏭️ Skipped: {len(results['skipped'])}")
        print(f"  ❌ Failed: {len(results['failed'])}")
        
        return results
    
    def _format_version_name(self, format_str, date_obj):
        """
        Format version name using date components
        
        Supports placeholders:
        - {date} -> full date (YYYY-MM-DD)
        - {year} -> year (YYYY)
        - {month} -> month (MM)
        - {day} -> day (DD)
        - {month_name} -> month name (February)
        - {month_short} -> short month (Feb)
        
        Examples:
        - 'Release {date}' -> 'Release 2026-02-05'
        - 'v{year}.{month}.{day}' -> 'v2026.02.05'
        - 'Sprint {month_name} {day}' -> 'Sprint February 05'
        """
        return format_str.format(
            date=date_obj.strftime('%Y-%m-%d'),
            year=date_obj.strftime('%Y'),
            month=date_obj.strftime('%m'),
            day=date_obj.strftime('%d'),
            month_name=date_obj.strftime('%B'),
            month_short=date_obj.strftime('%b')
        )
    
    def create_version(self, project_key, version_name, release_date=None, description="", archived=False):
        """
        Create a single fixVersion in Jira
        
        Args:
            project_key: Jira project key (e.g., 'KAN')
            version_name: Name of the version (e.g., 'v2.1.0')
            release_date: Release date in YYYY-MM-DD format (optional)
            description: Version description (optional)
            archived: Whether to archive this version (default: False)
            
        Returns:
            True if created successfully, False if skipped or failed
        """
        try:
            # Navigate to project versions page
            versions_url = f"{self.base_url}/plugins/servlet/project-config/{project_key}/versions"
            print(f"  📍 Navigating to: {versions_url}")
            self.driver.get(versions_url)
            time.sleep(3)  # Wait for page load
            
            # Check if we're still logged in
            is_logged_in, _, _ = check_login_status(self.driver)
            if not is_logged_in:
                print("  ❌ Lost session. Please login again.")
                return False
            
            # Click "Create Version" button
            success = self._click_create_version_button()
            if not success:
                return False
            
            # Fill in version details
            success = self._fill_version_form(version_name, release_date, description, archived)
            if not success:
                return False
            
            # Submit the form
            success = self._submit_version_form()
            return success
            
        except Exception as e:
            print(f"  ❌ Error in create_version: {e}")
            return False
    
    def _click_create_version_button(self):
        """Find and click the Create Version button"""
        try:
            # Strategy 1: Look for button with specific text
            try:
                create_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create version') or contains(text(), 'Create Version')]"))
                )
                create_btn.click()
                time.sleep(2)
                return True
            except:
                pass
            
            # Strategy 2: Look for button with data-testid
            try:
                create_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid*='create-version']")
                create_btn.click()
                time.sleep(2)
                return True
            except:
                pass
            
            # Strategy 3: Look for any button with "version" and "create" nearby
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for btn in buttons:
                    text = btn.text.lower()
                    if 'create' in text and 'version' in text:
                        btn.click()
                        time.sleep(2)
                        return True
            except:
                pass
            
            print("  ❌ Could not find 'Create Version' button")
            return False
            
        except Exception as e:
            print(f"  ❌ Error clicking create button: {e}")
            return False
    
    def _fill_version_form(self, version_name, release_date, description, archived):
        """Fill in the version creation form"""
        try:
            # Wait for form to appear
            time.sleep(1)
            
            # Fill version name
            try:
                name_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'version-name'))
                )
                name_field.clear()
                name_field.send_keys(version_name)
                print(f"  ✏️ Set name: {version_name}")
            except:
                # Try alternative selector
                try:
                    name_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='name']")
                    name_field.clear()
                    name_field.send_keys(version_name)
                    print(f"  ✏️ Set name: {version_name}")
                except Exception as e:
                    print(f"  ❌ Could not find version name field: {e}")
                    return False
            
            # Fill description if provided
            if description:
                try:
                    desc_field = self.driver.find_element(By.ID, 'version-description')
                    desc_field.clear()
                    desc_field.send_keys(description)
                    print(f"  ✏️ Set description: {description}")
                except:
                    try:
                        desc_field = self.driver.find_element(By.CSS_SELECTOR, "textarea[name='description']")
                        desc_field.clear()
                        desc_field.send_keys(description)
                        print(f"  ✏️ Set description: {description}")
                    except:
                        print("  ⚠️ Could not find description field (may not exist)")
            
            # Set release date if provided using datepicker
            if release_date:
                try:
                    # Click the release date field to open datepicker
                    date_field = self.driver.find_element(By.ID, 'version-releaseddate')
                    date_field.click()
                    time.sleep(1)
                    
                    # Parse the date
                    from datetime import datetime
                    date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                    
                    # Format for Jira: dd/MMM/yy (e.g., 26/Feb/26)
                    jira_date = date_obj.strftime('%d/%b/%y')
                    
                    # Clear and enter the date
                    date_field.clear()
                    date_field.send_keys(jira_date)
                    date_field.send_keys(Keys.RETURN)
                    print(f"  📅 Set release date: {jira_date}")
                    time.sleep(0.5)
                except:
                    try:
                        date_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='releaseDate']")
                        date_field.click()
                        time.sleep(1)
                        from datetime import datetime
                        date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                        jira_date = date_obj.strftime('%d/%b/%y')
                        date_field.clear()
                        date_field.send_keys(jira_date)
                        date_field.send_keys(Keys.RETURN)
                        print(f"  📅 Set release date: {jira_date}")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"  ⚠️ Could not set release date: {e}")
            
            # Set archived status if needed
            if archived:
                try:
                    archive_checkbox = self.driver.find_element(By.ID, 'version-archived')
                    if not archive_checkbox.is_selected():
                        archive_checkbox.click()
                        print("  📦 Marked as archived")
                except:
                    print("  ⚠️ Could not find archive checkbox")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error filling form: {e}")
            return False
    
    def _submit_version_form(self):
        """Submit the version creation form"""
        try:
            # Strategy 1: Look for submit button by ID
            try:
                submit_btn = self.driver.find_element(By.ID, 'version-add-submit')
                submit_btn.click()
                time.sleep(2)
                return True
            except:
                pass
            
            # Strategy 2: Look for button with "Create" or "Add" text
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for btn in buttons:
                    text = btn.text.lower()
                    if text in ['create', 'add', 'submit', 'save']:
                        btn.click()
                        time.sleep(2)
                        return True
            except:
                pass
            
            # Strategy 3: Try Enter key on focused element
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                time.sleep(2)
                return True
            except:
                pass
            
            print("  ❌ Could not find submit button")
            return False
            
        except Exception as e:
            print(f"  ❌ Error submitting form: {e}")
            return False
    
    def list_existing_versions(self, project_key=None):
        """
        List all existing versions for a project
        
        Args:
            project_key: Jira project key (uses first from config if None)
            
        Returns:
            List of version names
        """
        if project_key is None:
            project_key = self.config['jira']['project_keys'][0]
        
        try:
            versions_url = f"{self.base_url}/plugins/servlet/project-config/{project_key}/versions"
            self.driver.get(versions_url)
            time.sleep(3)
            
            # Try to find version names in the page
            versions = []
            try:
                version_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='version']")
                for elem in version_elements:
                    version_name = elem.text.strip()
                    if version_name:
                        versions.append(version_name)
            except:
                print("⚠️ Could not parse version list from page")
            
            return versions
            
        except Exception as e:
            print(f"❌ Error listing versions: {e}")
            return []
