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
        self.logger.info(f"[SNOW] Base URL: '{self.base_url}'")
        if not self.base_url:
            self.logger.error("[SNOW] ERROR: ServiceNow URL is empty or not configured!")
            self.logger.error("[SNOW] Please configure ServiceNow URL in Integrations tab")
        
    def login_check(self):
        """Check if logged into ServiceNow"""
        try:
            current_url = self.driver.current_url
            if 'service-now.com' in current_url and 'login' in current_url.lower():
                self.logger.warning("ServiceNow login required")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error checking ServiceNow login: {e}")
            return False
    
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
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "problem.short_description"))
            )
            
            if not self.login_check():
                self.logger.error("ServiceNow login required")
                return False
                
            return True
            
        except TimeoutException:
            self.logger.error(f"Timeout loading PRB {prb_number}")
            return False
        except Exception as e:
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
        """Get value from a ServiceNow form field"""
        try:
            element = self.driver.find_element(By.ID, field_id)
            
            if element.tag_name == 'select':
                from selenium.webdriver.support.ui import Select
                select = Select(element)
                return select.first_selected_option.text
            elif element.tag_name == 'textarea':
                return element.get_attribute('value') or ''
            else:
                return element.get_attribute('value') or ''
                
        except NoSuchElementException:
            self.logger.warning(f"Field not found: {field_id}")
            return ''
        except Exception as e:
            self.logger.error(f"Error reading field {field_id}: {e}")
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
