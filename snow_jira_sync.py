"""
ServiceNow-Jira Sync Orchestrator
Manages the workflow of creating Jira issues from ServiceNow PRBs
"""
import logging
import time
from servicenow_scraper import ServiceNowScraper
from jira_automator import JiraAutomator

class SnowJiraSync:
    """Orchestrates the ServiceNow to Jira automation workflow"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.snow = ServiceNowScraper(driver, config)
        self.jira = JiraAutomator(driver, config)
        self.logger = logging.getLogger(__name__)
        
    def validate_prb(self, prb_number):
        """
        Validate PRB exists and extract basic data
        
        Args:
            prb_number: PRB number to validate
            
        Returns:
            dict: {'success': bool, 'data': {...}, 'incidents': [...], 'error': str}
        """
        try:
            if not self.snow.navigate_to_prb(prb_number):
                return {
                    'success': False,
                    'error': f'Could not navigate to PRB {prb_number}. Check if it exists and you are logged in.'
                }
            
            prb_data = self.snow.extract_prb_data()
            if not prb_data:
                return {
                    'success': False,
                    'error': 'Failed to extract PRB data'
                }
            
            incidents = self.snow.extract_incident_numbers()
            
            return {
                'success': True,
                'data': prb_data,
                'incidents': incidents
            }
            
        except Exception as e:
            self.logger.error(f"Error validating PRB {prb_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_jira_issues(self, prb_data, selected_inc):
        """
        Create Jira Defect and Story from PRB data
        
        Args:
            prb_data: PRB data dict from ServiceNow
            selected_inc: Selected incident number (e.g., 'INC0123456')
            
        Returns:
            dict: {'success': bool, 'defect_key': str, 'story_key': str, 'error': str}
        """
        try:
            defect_key = self._create_defect(prb_data, selected_inc)
            if not defect_key:
                return {
                    'success': False,
                    'error': 'Failed to create Jira Defect'
                }
            
            self.logger.info(f"Created Jira Defect: {defect_key}")
            
            story_key = self._create_story(defect_key, prb_data, selected_inc)
            if not story_key:
                return {
                    'success': False,
                    'defect_key': defect_key,
                    'error': 'Failed to create Jira Story (Defect was created)'
                }
            
            self.logger.info(f"Created Jira Story: {story_key}")
            
            return {
                'success': True,
                'defect_key': defect_key,
                'story_key': story_key
            }
            
        except Exception as e:
            self.logger.error(f"Error creating Jira issues: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_prb_to_jira(self, prb_number, selected_inc):
        """
        Complete workflow: validate PRB, create Jira issues, update ServiceNow
        
        Args:
            prb_number: PRB number
            selected_inc: Selected incident number
            
        Returns:
            dict: Complete result with all keys and errors
        """
        try:
            validation = self.validate_prb(prb_number)
            if not validation['success']:
                return validation
            
            prb_data = validation['data']
            
            result = self.create_jira_issues(prb_data, selected_inc)
            if not result['success']:
                return result
            
            defect_key = result['defect_key']
            
            update_success = self.snow.update_prb_problem_statement(prb_number, defect_key)
            if not update_success:
                self.logger.warning(f"Failed to update ServiceNow PRB {prb_number}")
                result['warning'] = 'Jira issues created but ServiceNow update failed'
            
            result['prb_updated'] = update_success
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in sync workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_defect(self, prb_data, selected_inc):
        """Create Jira Defect from PRB data"""
        try:
            jira_project = self.config.get('servicenow', {}).get('jira_project', 'PROJ')
            
            summary = f"{selected_inc}: {prb_data['prb_number']}: {prb_data['short_description']}"
            
            field_mapping = self.config.get('servicenow', {}).get('field_mapping', {})
            
            custom_fields = {}
            if field_mapping.get('configuration_item'):
                custom_fields[field_mapping['configuration_item']] = prb_data.get('configuration_item', '')
            if field_mapping.get('impact'):
                custom_fields[field_mapping['impact']] = prb_data.get('impact', '')
            if field_mapping.get('urgency'):
                custom_fields[field_mapping['urgency']] = prb_data.get('urgency', '')
            if field_mapping.get('problem_category'):
                custom_fields[field_mapping['problem_category']] = prb_data.get('problem_category', '')
            if field_mapping.get('detection'):
                custom_fields[field_mapping['detection']] = prb_data.get('detection', '')
            
            defect_url = f"{self.jira.base_url}/secure/CreateIssue!default.jspa?pid={jira_project}"
            self.driver.get(defect_url)
            time.sleep(2)
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            issue_type_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "issuetype-field"))
            )
            
            from selenium.webdriver.support.ui import Select
            issue_type_select = Select(issue_type_field)
            issue_type_select.select_by_visible_text("Bug")
            
            summary_field = self.driver.find_element(By.ID, "summary")
            summary_field.clear()
            summary_field.send_keys(summary)
            
            description_field = self.driver.find_element(By.ID, "description")
            description_field.clear()
            description_field.send_keys(prb_data.get('description', ''))
            
            priority_value = prb_data.get('priority', '3')
            priority_mapping = {'1': 'Highest', '2': 'High', '3': 'Medium', '4': 'Low', '5': 'Lowest'}
            priority_field = self.driver.find_element(By.ID, "priority-field")
            priority_select = Select(priority_field)
            priority_select.select_by_visible_text(priority_mapping.get(priority_value, 'Medium'))
            
            for field_id, value in custom_fields.items():
                if value:
                    try:
                        custom_field = self.driver.find_element(By.ID, field_id)
                        custom_field.clear()
                        custom_field.send_keys(value)
                    except Exception as e:
                        self.logger.warning(f"Could not set custom field {field_id}: {e}")
            
            create_button = self.driver.find_element(By.ID, "create-issue-submit")
            create_button.click()
            
            time.sleep(3)
            
            issue_key_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "key-val"))
            )
            defect_key = issue_key_elem.text.strip()
            
            return defect_key
            
        except Exception as e:
            self.logger.error(f"Error creating Jira Defect: {e}")
            return None
    
    def _create_story(self, defect_key, prb_data, selected_inc):
        """Clone Defect to Story with [SL] prefix"""
        try:
            defect_url = f"{self.jira.base_url}/browse/{defect_key}"
            self.driver.get(defect_url)
            time.sleep(2)
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.action_chains import ActionChains
            
            more_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "opsbar-operations_more"))
            )
            more_button.click()
            
            clone_link = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "clone-issue"))
            )
            clone_link.click()
            
            time.sleep(2)
            
            from selenium.webdriver.support.ui import Select
            issue_type_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "issuetype-field"))
            )
            issue_type_select = Select(issue_type_field)
            issue_type_select.select_by_visible_text("Story")
            
            summary_field = self.driver.find_element(By.ID, "summary")
            current_summary = summary_field.get_attribute('value')
            summary_field.clear()
            summary_field.send_keys(f"[SL] {current_summary}")
            
            clone_button = self.driver.find_element(By.ID, "create-issue-submit")
            clone_button.click()
            
            time.sleep(3)
            
            issue_key_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "key-val"))
            )
            story_key = issue_key_elem.text.strip()
            
            link_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "link-issue"))
            )
            link_button.click()
            
            time.sleep(1)
            
            link_type_field = self.driver.find_element(By.ID, "link-type")
            link_type_select = Select(link_type_field)
            link_type_select.select_by_visible_text("relates to")
            
            issue_key_field = self.driver.find_element(By.ID, "jira-issue-keys")
            issue_key_field.send_keys(defect_key)
            
            link_submit_button = self.driver.find_element(By.ID, "link-issue-submit")
            link_submit_button.click()
            
            time.sleep(2)
            
            return story_key
            
        except Exception as e:
            self.logger.error(f"Error creating Story: {e}")
            return None
    
    def test_connection(self):
        """Test ServiceNow connection"""
        try:
            if not self.snow.base_url:
                return {
                    'success': False,
                    'error': 'ServiceNow URL not configured'
                }
            
            self.driver.get(self.snow.base_url)
            time.sleep(2)
            
            if self.snow.login_check():
                return {
                    'success': True,
                    'message': 'Connected to ServiceNow'
                }
            else:
                return {
                    'success': False,
                    'error': 'Not logged in to ServiceNow'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
