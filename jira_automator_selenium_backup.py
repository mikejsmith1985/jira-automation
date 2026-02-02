"""
Jira automation module - Playwright version
Handles Jira ticket updates via browser automation

This file is like a robot that knows how to use Jira through a web browser.
Instead of clicking buttons yourself, this robot clicks them for you!

Think of it like teaching a friend how to use Jira:
1. "Go to this ticket"
2. "Click the comment box"
3. "Type this message"
4. "Click save"

The robot (Playwright) does exactly what you tell it, step by step.
"""

class JiraAutomator:
    """
    The main robot that updates Jira tickets
    
    This class is like a smart assistant that knows how to:
    - Add comments to tickets
    - Change ticket fields (like adding a PR link)
    - Add labels to tickets
    - Move tickets to different statuses (like "In Review")
    """
    
    def __init__(self, page, config):
        """
        Set up the robot when it's first created
        
        Args:
            page: Playwright Page object (like a steering wheel for the browser)
            config: A dictionary with all the settings (like Jira URL, field names, etc)
        """
        self.page = page  # The browser page we'll use
        self.config = config  # All our settings
        self.base_url = config['jira']['base_url']  # Like "https://your-company.atlassian.net"
        
    def update_ticket(self, ticket_key, updates):
        """
        Update a Jira ticket with various changes
        
        This is the main function that does all the work. You give it a ticket
        (like "ABC-123") and a list of things to change, and it does them all!
        
        Args:
            ticket_key: The ticket to update (like "ABC-123")
            updates: A dictionary of things to change, like:
                {
                    'comment': 'This is a comment',
                    'fields': {
                        'customfield_10001': 'https://github.com/...',
                        'customfield_10002': 'Some other value'
                    },
                    'labels': ['has-pr', 'reviewed'],  # Can add multiple labels!
                    'status': 'In Review'
                }
        
        Returns:
            True if everything worked, False if something went wrong
        """
        try:
            # Step 1: Go to the ticket page
            # Like typing "https://jira.com/browse/ABC-123" in your browser
            ticket_url = f"{self.base_url}/browse/{ticket_key}"
            self.driver.get(ticket_url)
            time.sleep(2)  # Wait 2 seconds for the page to load
            
            success = True  # Keep track of whether everything works
            
            # Step 2: Add comment if requested
            if updates.get('comment'):
                success = success and self._add_comment(updates['comment'])
            
            # Step 3: Update custom fields if requested
            # NEW: Can now update MULTIPLE fields at once!
            if updates.get('fields'):
                success = success and self._update_fields(updates['fields'])
            
            # OLD WAY (still supported for backwards compatibility):
            # if updates.get('pr_field'):
            #     success = success and self._update_pr_field(updates['pr_field'])
            
            # Step 4: Add labels if requested
            # NEW: Can now add MULTIPLE labels at once!
            if updates.get('labels'):
                # If it's a list, add all of them
                if isinstance(updates['labels'], list):
                    for label in updates['labels']:
                        success = success and self._add_label(label)
                # If it's just one label (string), add it
                else:
                    success = success and self._add_label(updates['labels'])
            
            # OLD WAY (still supported):
            if updates.get('label'):
                success = success and self._add_label(updates['label'])
            
            # Step 5: Change status if requested
            if updates.get('status'):
                success = success and self._transition_status(updates['status'])
            
            return success
            
        except Exception as e:
            # If anything goes wrong, print the error and return False
            print(f"Error updating ticket {ticket_key}: {e}")
            return False
    
    def _add_comment(self, comment_text):
        """
        Add a comment to the current ticket
        
        This function tries THREE different ways to add a comment, because
        different versions of Jira have different button layouts. It's like
        trying three different keys to open a door - one of them should work!
        
        Args:
            comment_text: The message to post as a comment
            
        Returns:
            True if the comment was added, False otherwise
        """
        try:
            # Strategy 1: Try to find a comment box that's already visible
            # This works on older Jira versions
            try:
                # Look for a text box with id="comment"
                comment_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'comment'))
                )
                comment_field.click()  # Click it to make sure it's active
                time.sleep(0.5)  # Wait half a second
                comment_field.send_keys(comment_text)  # Type the comment
                
                # Submit with Ctrl+Enter (Jira shortcut to save)
                comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                time.sleep(1)  # Wait for it to save
                return True
            except:
                pass  # If that didn't work, try the next strategy
            
            # Strategy 2: Click "Add a comment" button first, THEN type
            # This works when the comment box is hidden until you click a button
            try:
                # Find and click the "Add comment" button
                comment_btn = self.driver.find_element(By.ID, 'footer-comment-button')
                comment_btn.click()
                time.sleep(1)  # Wait for comment box to appear
                
                # Now find the comment box and type
                comment_field = self.driver.find_element(By.ID, 'comment')
                comment_field.send_keys(comment_text)
                comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                time.sleep(1)
                return True
            except:
                pass  # Try next strategy
            
            # Strategy 3: Modern Jira interface (cloud version)
            # Looks for a textarea with "comment" in the placeholder text
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
            
            # If we get here, none of the strategies worked :(
            print("Could not add comment - all strategies failed")
            return False
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def _update_fields(self, fields):
        """
        Update multiple custom fields at once
        
        NEW FUNCTION! This lets you update as many fields as you want in one go.
        Each field has an ID (like "customfield_10001") and a value.
        
        Args:
            fields: A dictionary like:
                {
                    'customfield_10001': 'https://github.com/pr/123',
                    'customfield_10002': 'v2.0.0',
                    'fixVersion': 'Sprint 23'
                }
        
        Returns:
            True if all fields were updated, False if any failed
        """
        try:
            # Step 1: Click the "Edit" button to put the ticket in edit mode
            edit_btn = self.driver.find_element(By.ID, 'edit-issue')
            edit_btn.click()
            time.sleep(2)  # Wait for edit form to load
            
            all_success = True  # Track if all fields update successfully
            
            # Step 2: Update each field one by one
            for field_id, field_value in fields.items():
                try:
                    # Try to find the field by its ID
                    field_element = self.driver.find_element(By.ID, field_id)
                    field_element.clear()  # Clear old value
                    field_element.send_keys(field_value)  # Type new value
                    print(f"  ✓ Updated field {field_id} = {field_value}")
                    
                except Exception as e:
                    print(f"  ✗ Could not update field {field_id}: {e}")
                    all_success = False
            
            # Step 3: Save all the changes by clicking "Update"
            update_btn = self.driver.find_element(By.ID, 'edit-issue-submit')
            update_btn.click()
            time.sleep(2)  # Wait for changes to save
            
            return all_success
            
        except Exception as e:
            print(f"Error updating fields: {e}")
            return False
    
    def _update_pr_field(self, pr_url):
        """
        Update the PR link custom field (OLD FUNCTION - kept for compatibility)
        
        This is the old way of updating just ONE field. Still works, but
        you should use _update_fields() instead if you need to update multiple things.
        
        Args:
            pr_url: The GitHub PR URL to save
            
        Returns:
            True if successful, False otherwise
        """
        # Just use the new multi-field function with one field
        field_id = self.config['jira']['pr_link_field']
        return self._update_fields({field_id: pr_url})
    
    def _add_label(self, label):
        """
        Add a label to the ticket
        
        Labels are like tags - they help organize tickets. For example:
        - "has-pr" means this ticket has a pull request
        - "reviewed" means someone reviewed it
        - "urgent" means it needs attention soon
        
        Args:
            label: The label text to add (like "has-pr")
            
        Returns:
            True if the label was added, False otherwise
        """
        try:
            # Click on the labels area to open it
            labels_elem = self.driver.find_element(By.ID, 'labels-field')
            labels_elem.click()
            time.sleep(0.5)
            
            # Type the label name
            label_input = self.driver.find_element(By.ID, 'labels-textarea')
            label_input.send_keys(label)
            label_input.send_keys(Keys.ENTER)  # Press Enter to add it
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error adding label '{label}': {e}")
            return False
    
    def _transition_status(self, target_status):
        """
        Move a ticket to a different status
        
        In Jira, tickets have statuses like "To Do", "In Progress", "Done".
        This function clicks the button to move a ticket from one status to another.
        
        For example: Moving from "To Do" → "In Review" when a PR is opened
        
        Args:
            target_status: The status to move to (like "In Review" or "Done")
            
        Returns:
            True if the status was changed, False otherwise
        """
        try:
            # Find all buttons on the page
            workflow_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[type="button"]')
            
            # Look through each button to find one that matches our target status
            for btn in workflow_btns:
                # Check if the button text contains our target status
                # (We use .lower() to ignore uppercase/lowercase differences)
                if target_status.lower() in btn.text.lower():
                    btn.click()  # Click the button!
                    time.sleep(2)
                    
                    # Sometimes Jira shows a confirmation popup - if so, click "OK"
                    try:
                        confirm_btn = self.driver.find_element(By.ID, 'issue-workflow-transition-submit')
                        confirm_btn.click()
                        time.sleep(2)
                    except:
                        pass  # No popup, that's fine
                    
                    return True
            
            # If we get here, we never found a button with that status name
            print(f"Could not find transition button for: {target_status}")
            return False
            
        except Exception as e:
            print(f"Error transitioning status to '{target_status}': {e}")
            return False
