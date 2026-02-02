"""
ServiceNow scraper module
Handles data extraction from ServiceNow PRB tickets via browser automation
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ServiceNowScraper:
    """Scrapes data from ServiceNow Problem (PRB) tickets"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.base_url = config.get('servicenow', {}).get('url', '').strip()
        self.logger = logging.getLogger(__name__)
        
        # Log configuration for debugging
        self.logger.info(f"[SNOW] ServiceNowScraper initialized")
        # Normalize base_url - remove trailing slash to prevent double slashes
        self.base_url = self.base_url.rstrip('/') if self.base_url else ''
        self.logger.info(f"[SNOW] Base URL: '{self.base_url}'")
        if not self.base_url:
            self.logger.error("[SNOW] ERROR: ServiceNow URL is empty or not configured!")
            self.logger.error("[SNOW] Please configure ServiceNow URL in Integrations tab")
        
    def login_check(self):
        """Check if logged into ServiceNow"""
        try:
            current_url = self.driver.current_url
            # Only return False if explicitly on a login page
            # Don't fail if user is on valid ServiceNow pages
            if 'login' in current_url.lower() and 'service-now.com' in current_url:
                self.logger.warning("ServiceNow login page detected")
                return False
            return True  # Assume logged in if not on login page
        except Exception as e:
            self.logger.error(f"Error checking ServiceNow login: {e}")
            return True  # Don't fail on error, assume logged in
    
    def navigate_to_prb(self, prb_number):
        """
        Navigate to a specific PRB ticket
        
        Args:
            prb_number: The PRB number (e.g., 'PRB0123456')
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            if not self.base_url:
                raise ValueError("ServiceNow URL not configured")
            
            prb_url = f"{self.base_url}/problem.do?sysparm_query=number={prb_number}"
            self.logger.info(f"Navigating to PRB: {prb_url}")
            self.driver.get(prb_url)
            
            # Wait for page to fully load - ServiceNow is JavaScript-heavy
            self.logger.info("Waiting for page to load...")
            time.sleep(5)  # Increased from 3s - ServiceNow needs time for JS execution
            
            # Wait for body to be present (basic page load indicator)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                self.logger.error("Page body never loaded")
                return False
            
            # ServiceNow often uses iframes - try to switch to gsft_main iframe
            try:
                iframe = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "gsft_main"))
                )
                self.driver.switch_to.frame(iframe)
                self.logger.info("Switched to gsft_main iframe")
            except TimeoutException:
                self.logger.info("No gsft_main iframe found, staying in main context")
            except Exception as e:
                self.logger.warning(f"Could not switch to iframe: {e}")
            
            # Check if PRB is in page source first (fast check)
            if prb_number not in self.driver.page_source:
                self.logger.error(f"PRB {prb_number} not found in page source - wrong page?")
                return False
            
            self.logger.info(f"PRB {prb_number} confirmed in page source")
            
            # Wait for JavaScript to render form - use ONLY CSS/XPath (not By.ID with dots!)
            # Based on user's Chrome recording JSON showing exact selectors that work
            form_loaded = False
            wait_selectors = [
                # PRIMARY: CSS selectors for fields with dots (from recording)
                (By.CSS_SELECTOR, "[id='problem.short_description']"),
                (By.CSS_SELECTOR, "[id='problem.description']"),
                (By.CSS_SELECTOR, "[id='problem.number']"),
                # BACKUP: XPath selectors (also from recording)
                (By.XPATH, "//*[@id='problem.short_description']"),
                (By.XPATH, "//*[@id='problem.description']"),
                # FALLBACK: Modern UI without "problem." prefix
                (By.CSS_SELECTOR, "[id='short_description']"),
                (By.CSS_SELECTOR, "[id='description']"),
            ]
            
            # Reduced timeout: 3 seconds per selector (not 20!)
            for by, selector in wait_selectors:
                try:
                    self.logger.info(f"Waiting for element: {selector}")
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    self.logger.info(f"✓ Form loaded - found: {selector}")
                    form_loaded = True
                    break
                except TimeoutException:
                    continue
            
            if not form_loaded:
                # Debug: log all element IDs on page
                try:
                    all_ids = self.driver.find_elements(By.XPATH, "//*[@id]")
                    found_ids = [el.get_attribute("id") for el in all_ids[:20]]  # First 20
                    self.logger.warning(f"Form elements not found. IDs on page: {found_ids}")
                except:
                    pass
                
                # Save HTML for debugging
                try:
                    import os
                    debug_file = os.path.join(os.path.dirname(__file__), "snow_debug.html")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    self.logger.info(f"Saved page HTML to: {debug_file}")
                except Exception as e:
                    self.logger.warning(f"Could not save debug HTML: {e}")
                
                self.driver.switch_to.default_content()
                self.logger.error(f"Could not find form fields for {prb_number} (tried 7 selectors in 21s)")
                return False
            
            # Form loaded successfully
            return self.login_check()
            
        except TimeoutException:
            self.driver.switch_to.default_content()
            self.logger.error(f"Timeout loading PRB {prb_number}")
            return False
        except Exception as e:
            self.driver.switch_to.default_content()
            self.logger.error(f"Error navigating to PRB {prb_number}: {e}")
            return False
    
    def extract_prb_data(self):
        """
        Extract all relevant fields from the current PRB ticket
        
        Returns:
            dict: PRB data with keys matching ServiceNow field names
        """
        prb_data = {}
        
        try:
            prb_data['prb_number'] = self._get_field_value('problem.number')
            prb_data['short_description'] = self._get_field_value('problem.short_description')
            prb_data['description'] = self._get_field_value('problem.description')
            prb_data['configuration_item'] = self._get_field_value('sys_display.problem.cmdb_ci')
            prb_data['impact'] = self._get_field_value('problem.impact')
            prb_data['urgency'] = self._get_field_value('problem.urgency')
            prb_data['priority'] = self._get_field_value('problem.priority')
            prb_data['problem_category'] = self._get_field_value('problem.u_problem_category')
            prb_data['detection'] = self._get_field_value('problem.u_dectection')
            
            self.logger.info(f"Extracted PRB data: {prb_data.get('prb_number', 'Unknown')}")
            return prb_data
            
        except Exception as e:
            self.logger.error(f"Error extracting PRB data: {e}")
            return None
    
    def _get_field_value(self, field_id):
        """Get value from a ServiceNow form field
        
        Uses CSS selectors to handle dotted IDs properly (By.ID doesn't work reliably)
        Based on user's Chrome recording showing fields like 'problem.short_description'
        """
        # Try multiple variations of the field ID
        field_variations = [
            field_id,  # Original (e.g., "problem.short_description")
        ]
        
        # If field has "problem." prefix, also try without it
        if field_id.startswith('problem.'):
            short_id = field_id.replace('problem.', '', 1)
            field_variations.append(short_id)  # e.g., "short_description"
        
        # If field has dots, also try with underscores (some ServiceNow configs)
        if '.' in field_id:
            underscore_id = field_id.replace('.', '_')
            field_variations.append(underscore_id)  # e.g., "problem_short_description"
        
        self.logger.debug(f"Looking for field: {field_id} (variations: {field_variations})")
        
        for variation in field_variations:
            try:
                # Use CSS selector for dotted IDs (more reliable than By.ID)
                element = self.driver.find_element(By.CSS_SELECTOR, f"[id='{variation}']")
                
                if element.tag_name == 'select':
                    from selenium.webdriver.support.ui import Select
                    select = Select(element)
                    return select.first_selected_option.text
                elif element.tag_name == 'textarea':
                    return element.get_attribute('value') or ''
                else:
                    return element.get_attribute('value') or ''
                    
            except NoSuchElementException:
                continue  # Try next variation
            except Exception as e:
                self.logger.debug(f"Error reading field {variation}: {e}")
                continue
        
        # None of the variations worked
        self.logger.warning(f"Field not found: {field_id} (tried: {', '.join(field_variations)})")
        return ''
    
    def extract_incident_numbers(self):
        """
        Navigate to Incidents tab and extract related INC numbers
        
        Returns:
            list: List of dicts with INC data [{'number': 'INC0123456', 'summary': '...', ...}, ...]
        """
        incidents = []
        
        try:
            incident_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Incidents')]"))
            )
            incident_tab.click()
            time.sleep(2)
            
            self.driver.switch_to.frame(self.driver.find_element(By.ID, "gsft_main"))
            
            incident_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list_table"))
            )
            
            rows = incident_table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        inc_number_elem = cells[0].find_element(By.TAG_NAME, "a")
                        inc_number = inc_number_elem.text.strip()
                        
                        inc_summary = ''
                        if len(cells) >= 3:
                            inc_summary = cells[2].text.strip()
                        
                        if inc_number.startswith('INC'):
                            incidents.append({
                                'number': inc_number,
                                'summary': inc_summary
                            })
                            self.logger.info(f"Found incident: {inc_number}")
                            
                except Exception as e:
                    self.logger.warning(f"Error parsing incident row: {e}")
                    continue
            
            self.driver.switch_to.default_content()
            
            if not incidents:
                self.logger.warning("No incidents found in Incidents tab")
            
            return incidents
            
        except TimeoutException:
            self.logger.error("Timeout finding Incidents tab")
            self.driver.switch_to.default_content()
            return []
        except Exception as e:
            self.logger.error(f"Error extracting incident numbers: {e}")
            self.driver.switch_to.default_content()
            return []
    
    def update_prb_problem_statement(self, prb_number, jira_key):
        """
        Update the PRB Problem Statement with Jira key
        
        Args:
            prb_number: PRB number to update
            jira_key: Jira key to append (e.g., 'PROJ-123')
            
        Returns:
            bool: True if update successful
        """
        try:
            if not self.navigate_to_prb(prb_number):
                return False
            
            problem_statement_field = self.driver.find_element(By.ID, "problem.short_description")
            current_value = problem_statement_field.get_attribute('value')
            
            if jira_key in current_value:
                self.logger.info(f"Jira key {jira_key} already in Problem Statement")
                return True
            
            new_value = f"{current_value} - {jira_key}"
            
            problem_statement_field.clear()
            problem_statement_field.send_keys(new_value)
            
            save_button = self.driver.find_element(By.ID, "sysverb_update")
            save_button.click()
            
            time.sleep(2)
            
            self.logger.info(f"Updated PRB {prb_number} with Jira key {jira_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating PRB {prb_number}: {e}")
            return False
