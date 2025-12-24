"""
Jira automation module
Handles Jira ticket updates via browser automation
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class JiraAutomator:
    """Automates Jira ticket updates"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.base_url = config['jira']['base_url']
        
    def update_ticket(self, ticket_key, updates):
        """
        Update a Jira ticket with various changes
        
        updates = {
            'comment': 'Comment text',
            'status': 'In Review',
            'label': 'has-pr',
            'pr_field': 'https://github.com/...'
        }
        """
        try:
            # Navigate to ticket
            ticket_url = f"{self.base_url}/browse/{ticket_key}"
            self.driver.get(ticket_url)
            time.sleep(2)
            
            success = True
            
            # Add comment
            if updates.get('comment'):
                success = success and self._add_comment(updates['comment'])
            
            # Update custom field (PR link)
            if updates.get('pr_field'):
                success = success and self._update_pr_field(updates['pr_field'])
            
            # Add label
            if updates.get('label'):
                success = success and self._add_label(updates['label'])
            
            # Transition status
            if updates.get('status'):
                success = success and self._transition_status(updates['status'])
            
            return success
        except Exception as e:
            print(f"Error updating ticket {ticket_key}: {e}")
            return False
    
    def _add_comment(self, comment_text):
        """Add a comment to the current ticket"""
        try:
            # Strategy 1: Find comment textarea
            try:
                comment_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'comment'))
                )
                comment_field.click()
                time.sleep(0.5)
                comment_field.send_keys(comment_text)
                
                # Submit with Ctrl+Enter
                comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                time.sleep(1)
                return True
            except:
                pass
            
            # Strategy 2: Click "Add a comment" button first
            try:
                comment_btn = self.driver.find_element(By.ID, 'footer-comment-button')
                comment_btn.click()
                time.sleep(1)
                
                comment_field = self.driver.find_element(By.ID, 'comment')
                comment_field.send_keys(comment_text)
                comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                time.sleep(1)
                return True
            except:
                pass
            
            # Strategy 3: Modern Jira interface
            try:
                comment_field = self.driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder*="comment" i]')
                comment_field.click()
                time.sleep(0.5)
                comment_field.send_keys(comment_text)
                comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                time.sleep(1)
                return True
            except:
                pass
            
            print("Could not add comment - all strategies failed")
            return False
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def _update_pr_field(self, pr_url):
        """Update the PR link custom field"""
        try:
            # Click edit button
            edit_btn = self.driver.find_element(By.ID, 'edit-issue')
            edit_btn.click()
            time.sleep(2)
            
            # Find PR field by configured field ID or name
            field_name = self.config['jira']['pr_link_field_name']
            
            try:
                # Try to find field by label
                field_label = self.driver.find_element(By.XPATH, f"//label[contains(text(), '{field_name}')]")
                field_id = field_label.get_attribute('for')
                pr_field = self.driver.find_element(By.ID, field_id)
                pr_field.clear()
                pr_field.send_keys(pr_url)
            except:
                # Fallback: try by field ID directly
                field_id = self.config['jira']['pr_link_field']
                pr_field = self.driver.find_element(By.ID, field_id)
                pr_field.clear()
                pr_field.send_keys(pr_url)
            
            # Save changes
            update_btn = self.driver.find_element(By.ID, 'edit-issue-submit')
            update_btn.click()
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"Error updating PR field: {e}")
            return False
    
    def _add_label(self, label):
        """Add a label to the ticket"""
        try:
            # Click on labels field
            labels_elem = self.driver.find_element(By.ID, 'labels-field')
            labels_elem.click()
            time.sleep(0.5)
            
            # Type label
            label_input = self.driver.find_element(By.ID, 'labels-textarea')
            label_input.send_keys(label)
            label_input.send_keys(Keys.ENTER)
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error adding label: {e}")
            return False
    
    def _transition_status(self, target_status):
        """Transition ticket to a new status"""
        try:
            # Find workflow buttons
            workflow_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[type="button"]')
            
            for btn in workflow_btns:
                if target_status.lower() in btn.text.lower():
                    btn.click()
                    time.sleep(2)
                    
                    # Handle any confirmation dialogs
                    try:
                        confirm_btn = self.driver.find_element(By.ID, 'issue-workflow-transition-submit')
                        confirm_btn.click()
                        time.sleep(2)
                    except:
                        pass
                    
                    return True
            
            print(f"Could not find transition button for: {target_status}")
            return False
            
        except Exception as e:
            print(f"Error transitioning status: {e}")
            return False
