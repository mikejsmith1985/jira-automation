"""
Jira Data Updater
Updates Jira tickets via Selenium WebDriver
"""
import time
from typing import Dict, List, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class JiraUpdater:
    """
    Update Jira tickets using Selenium.
    Provides single and bulk update capabilities.
    """
    
    def __init__(self, driver, config: Dict, scraper=None):
        self.driver = driver
        self.config = config
        self.base_url = config.get('base_url', '').rstrip('/')
        self.wait_timeout = config.get('wait_timeout', 10)
        self.scraper = scraper
    
    def _wait_for_element(self, by: By, value: str, timeout: int = None) -> Any:
        """Wait for element to be present"""
        timeout = timeout or self.wait_timeout
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = None) -> Any:
        """Wait for element to be clickable"""
        timeout = timeout or self.wait_timeout
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            return None
    
    def navigate_to_issue(self, issue_key: str) -> bool:
        """Navigate to an issue page"""
        try:
            issue_url = f"{self.base_url}/browse/{issue_key}"
            self.driver.get(issue_url)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error navigating to issue {issue_key}: {e}")
            return False
    
    def update_issue(self, issue_key: str, updates: Dict) -> Dict:
        """
        Update a single issue with specified changes.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            updates: Dictionary of updates:
                {
                    'comment': str,
                    'status': str,
                    'labels': [str],
                    'assignee': str,
                    'priority': str,
                    'fields': {'field_id': value}
                }
                
        Returns:
            {'success': bool, 'applied': [...], 'errors': [...]}
        """
        result = {
            'success': True,
            'issue_key': issue_key,
            'applied': [],
            'errors': []
        }
        
        if not self.navigate_to_issue(issue_key):
            result['success'] = False
            result['errors'].append('Could not navigate to issue')
            return result
        
        if 'comment' in updates and updates['comment']:
            if self.add_comment(issue_key, updates['comment']):
                result['applied'].append('comment')
            else:
                result['errors'].append('Failed to add comment')
        
        if 'status' in updates and updates['status']:
            if self.transition_status(issue_key, updates['status']):
                result['applied'].append('status')
            else:
                result['errors'].append(f"Failed to transition to {updates['status']}")
        
        if 'labels' in updates and updates['labels']:
            for label in updates['labels']:
                if self.add_label(issue_key, label):
                    result['applied'].append(f'label:{label}')
                else:
                    result['errors'].append(f'Failed to add label {label}')
        
        if 'assignee' in updates and updates['assignee']:
            if self.update_assignee(issue_key, updates['assignee']):
                result['applied'].append('assignee')
            else:
                result['errors'].append('Failed to update assignee')
        
        if 'priority' in updates and updates['priority']:
            if self.update_priority(issue_key, updates['priority']):
                result['applied'].append('priority')
            else:
                result['errors'].append('Failed to update priority')
        
        if 'fields' in updates and updates['fields']:
            for field_id, value in updates['fields'].items():
                if self.update_field(issue_key, field_id, value):
                    result['applied'].append(f'field:{field_id}')
                else:
                    result['errors'].append(f'Failed to update field {field_id}')
        
        result['success'] = len(result['errors']) == 0
        return result
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue"""
        try:
            comment_btn = self._wait_for_clickable(
                By.CSS_SELECTOR,
                '#footer-comment-button, [data-test-id="issue.activity.add-comment"]'
            )
            
            if comment_btn:
                comment_btn.click()
                time.sleep(1)
            
            comment_field = self._wait_for_element(
                By.CSS_SELECTOR,
                '#comment, [data-test-id="issue.activity.comment-form-field"]'
            )
            
            if not comment_field:
                text_area = self._wait_for_element(By.CSS_SELECTOR, 'textarea[id*="comment"]')
                if text_area:
                    comment_field = text_area
            
            if comment_field:
                comment_field.clear()
                comment_field.send_keys(comment)
                time.sleep(0.5)
                
                submit_btn = self._wait_for_clickable(
                    By.CSS_SELECTOR,
                    '#issue-comment-add-submit, [data-test-id="issue.activity.comment-save-button"]'
                )
                
                if submit_btn:
                    submit_btn.click()
                    time.sleep(1)
                    return True
                else:
                    comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                    time.sleep(1)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def transition_status(self, issue_key: str, target_status: str) -> bool:
        """Transition issue to a new status"""
        try:
            status_btn = self._wait_for_clickable(
                By.CSS_SELECTOR,
                '#status-val, [data-test-id="issue.views.issue-base.foundation.status.status-field-wrapper"]'
            )
            
            if status_btn:
                status_btn.click()
                time.sleep(1)
            
            transitions = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.aui-list-item-link, [data-test-id="issue.views.issue-base.foundation.status.status-field-wrapper--popup"] button'
            )
            
            for transition in transitions:
                if target_status.lower() in transition.text.lower():
                    transition.click()
                    time.sleep(1)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error transitioning status: {e}")
            return False
    
    def add_label(self, issue_key: str, label: str) -> bool:
        """Add a label to an issue"""
        try:
            labels_field = self._wait_for_clickable(
                By.CSS_SELECTOR,
                '#labels-val, [data-test-id="issue.views.field.multi-select.labels"]'
            )
            
            if labels_field:
                labels_field.click()
                time.sleep(0.5)
            
            label_input = self._wait_for_element(
                By.CSS_SELECTOR,
                '#labels-textarea, input[id*="labels"]'
            )
            
            if label_input:
                label_input.send_keys(label)
                time.sleep(0.5)
                label_input.send_keys(Keys.ENTER)
                time.sleep(0.5)
                
                try:
                    body = self.driver.find_element(By.TAG_NAME, 'body')
                    body.click()
                except:
                    pass
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error adding label: {e}")
            return False
    
    def update_assignee(self, issue_key: str, assignee: str) -> bool:
        """Update the assignee of an issue"""
        try:
            assignee_field = self._wait_for_clickable(
                By.CSS_SELECTOR,
                '#assignee-val, [data-test-id="issue.views.field.user.assignee"]'
            )
            
            if assignee_field:
                assignee_field.click()
                time.sleep(0.5)
            
            assignee_input = self._wait_for_element(
                By.CSS_SELECTOR,
                '#assignee-field, input[id*="assignee"]'
            )
            
            if assignee_input:
                assignee_input.clear()
                assignee_input.send_keys(assignee)
                time.sleep(1)
                
                suggestion = self._wait_for_clickable(
                    By.CSS_SELECTOR,
                    '.aui-list-item-link, [data-test-id="user-picker-option"]'
                )
                if suggestion:
                    suggestion.click()
                else:
                    assignee_input.send_keys(Keys.ENTER)
                
                time.sleep(0.5)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating assignee: {e}")
            return False
    
    def update_priority(self, issue_key: str, priority: str) -> bool:
        """Update the priority of an issue"""
        try:
            priority_field = self._wait_for_clickable(
                By.CSS_SELECTOR,
                '#priority-val'
            )
            
            if priority_field:
                priority_field.click()
                time.sleep(0.5)
            
            options = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.aui-list-item-link'
            )
            
            for option in options:
                if priority.lower() in option.text.lower():
                    option.click()
                    time.sleep(0.5)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating priority: {e}")
            return False
    
    def update_field(self, issue_key: str, field_id: str, value: Any) -> bool:
        """Update a specific field by ID"""
        try:
            field = self._wait_for_clickable(
                By.CSS_SELECTOR,
                f'#{field_id}-val, [data-field-id="{field_id}"]'
            )
            
            if field:
                field.click()
                time.sleep(0.5)
            
            input_field = self._wait_for_element(
                By.CSS_SELECTOR,
                f'#{field_id}, input[name="{field_id}"]'
            )
            
            if input_field:
                input_field.clear()
                input_field.send_keys(str(value))
                input_field.send_keys(Keys.ENTER)
                time.sleep(0.5)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating field {field_id}: {e}")
            return False
    
    def bulk_update(self, jql: str, updates: Dict, delay_between: float = 1.0) -> Dict:
        """
        Apply updates to all issues matching JQL.
        
        Args:
            jql: JQL query to find issues
            updates: Updates to apply to each issue
            delay_between: Delay between updates (seconds)
            
        Returns:
            {
                'success': bool,
                'total': int,
                'updated': int,
                'failed': int,
                'results': [...]
            }
        """
        result = {
            'success': True,
            'total': 0,
            'updated': 0,
            'failed': 0,
            'results': []
        }
        
        if not self.scraper:
            result['success'] = False
            result['errors'] = ['Scraper not available for bulk update']
            return result
        
        try:
            issues = self.scraper.execute_jql(jql)
            result['total'] = len(issues)
            
            for issue in issues:
                issue_key = issue['key']
                update_result = self.update_issue(issue_key, updates)
                
                result['results'].append(update_result)
                
                if update_result['success']:
                    result['updated'] += 1
                else:
                    result['failed'] += 1
                
                time.sleep(delay_between)
            
            result['success'] = result['failed'] == 0
            
        except Exception as e:
            result['success'] = False
            result['errors'] = [str(e)]
        
        return result
