"""
Jira Data Scraper
Extracts data from Jira via Selenium WebDriver
"""
import time
import re
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class JiraScraper:
    """
    Extract data from Jira using Selenium.
    Navigates Jira UI, executes searches, and parses HTML results.
    """
    
    def __init__(self, driver, config: Dict):
        self.driver = driver
        self.config = config
        self.base_url = config.get('base_url', '').rstrip('/')
        self.wait_timeout = config.get('wait_timeout', 10)
    
    def _wait_for_element(self, by: By, value: str, timeout: int = None) -> Any:
        """Wait for element to be present and return it"""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = None) -> Any:
        """Wait for element to be clickable and return it"""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def navigate_to_search(self) -> bool:
        """Navigate to Jira issue search page"""
        try:
            search_url = f"{self.base_url}/issues/"
            self.driver.get(search_url)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"Error navigating to search: {e}")
            return False
    
    def execute_jql(self, jql: str, max_results: int = 500) -> List[Dict]:
        """
        Execute JQL query and extract results.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to fetch
            
        Returns:
            List of issue dictionaries
        """
        issues = []
        
        try:
            # Use proper URL encoding for JQL
            jql_encoded = urllib.parse.quote(jql)
            search_url = f"{self.base_url}/issues/?jql={jql_encoded}"
            self.driver.get(search_url)
            time.sleep(2)
            
            page = 1
            while len(issues) < max_results:
                page_issues = self._parse_issue_list()
                
                if not page_issues:
                    break
                
                issues.extend(page_issues)
                
                if not self._go_to_next_page():
                    break
                
                page += 1
                time.sleep(1)
            
            return issues[:max_results]
            
        except Exception as e:
            print(f"Error executing JQL: {e}")
            return issues
    
    def _parse_issue_list(self) -> List[Dict]:
        """Parse issues from current search results page"""
        issues = []
        
        try:
            issue_rows = self.driver.find_elements(By.CSS_SELECTOR, '[data-issuekey]')
            
            if not issue_rows:
                issue_rows = self.driver.find_elements(By.CSS_SELECTOR, '.issue-list tr')
            
            for row in issue_rows:
                try:
                    issue = self._parse_issue_row(row)
                    if issue:
                        issues.append(issue)
                except Exception as e:
                    print(f"Error parsing issue row: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing issue list: {e}")
        
        return issues
    
    def _parse_issue_row(self, row) -> Optional[Dict]:
        """Parse a single issue row from search results"""
        try:
            issue_key = row.get_attribute('data-issuekey')
            if not issue_key:
                key_elem = row.find_element(By.CSS_SELECTOR, '.issuekey a, [data-issue-key]')
                issue_key = key_elem.text or key_elem.get_attribute('data-issue-key')
            
            if not issue_key:
                return None
            
            issue = {
                'key': issue_key,
                'summary': '',
                'status': '',
                'type': '',
                'priority': '',
                'assignee': '',
                'created': '',
                'updated': '',
                'epic_link': '',
                'story_points': 0,
                'labels': [],
                'links': []
            }
            
            try:
                summary_elem = row.find_element(By.CSS_SELECTOR, '.summary, [data-field-id="summary"]')
                issue['summary'] = summary_elem.text
            except:
                pass
            
            try:
                status_elem = row.find_element(By.CSS_SELECTOR, '.status, [data-field-id="status"]')
                issue['status'] = status_elem.text
            except:
                pass
            
            try:
                type_elem = row.find_element(By.CSS_SELECTOR, '.issuetype img, [data-field-id="issuetype"]')
                issue['type'] = type_elem.get_attribute('alt') or type_elem.text
            except:
                pass
            
            try:
                priority_elem = row.find_element(By.CSS_SELECTOR, '.priority img, [data-field-id="priority"]')
                issue['priority'] = priority_elem.get_attribute('alt') or priority_elem.text
            except:
                pass
            
            try:
                assignee_elem = row.find_element(By.CSS_SELECTOR, '.assignee, [data-field-id="assignee"]')
                issue['assignee'] = assignee_elem.text
            except:
                pass
            
            return issue
            
        except Exception as e:
            print(f"Error parsing issue row: {e}")
            return None
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, '.pagination-next:not(.disabled), [data-page="next"]')
            if next_btn and next_btn.is_enabled():
                next_btn.click()
                time.sleep(1)
                return True
        except:
            pass
        return False
    
    def get_issue_details(self, issue_key: str) -> Dict:
        """
        Get full details for a single issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            
        Returns:
            Complete issue dictionary with all fields
        """
        issue = {
            'key': issue_key,
            'summary': '',
            'description': '',
            'status': '',
            'type': '',
            'priority': '',
            'assignee': '',
            'reporter': '',
            'created': '',
            'updated': '',
            'resolved': '',
            'epic_link': '',
            'story_points': 0,
            'labels': [],
            'components': [],
            'fix_versions': [],
            'links': [],
            'comments': [],
            'custom_fields': {}
        }
        
        try:
            issue_url = f"{self.base_url}/browse/{issue_key}"
            self.driver.get(issue_url)
            time.sleep(2)
            
            try:
                summary = self.driver.find_element(By.CSS_SELECTOR, '#summary-val, [data-test-id="issue.views.issue-base.foundation.summary.heading"]')
                issue['summary'] = summary.text
            except:
                pass
            
            try:
                status = self.driver.find_element(By.CSS_SELECTOR, '#status-val, [data-test-id="issue.views.issue-base.foundation.status.status-field-wrapper"]')
                issue['status'] = status.text
            except:
                pass
            
            try:
                issue_type = self.driver.find_element(By.CSS_SELECTOR, '#type-val, [data-test-id="issue.views.issue-base.foundation.issue-type.icon"]')
                issue['type'] = issue_type.text or issue_type.get_attribute('alt')
            except:
                pass
            
            try:
                priority = self.driver.find_element(By.CSS_SELECTOR, '#priority-val')
                issue['priority'] = priority.text
            except:
                pass
            
            try:
                assignee = self.driver.find_element(By.CSS_SELECTOR, '#assignee-val, [data-test-id="issue.views.field.user.assignee"]')
                issue['assignee'] = assignee.text
            except:
                pass
            
            try:
                labels = self.driver.find_elements(By.CSS_SELECTOR, '#labels-val .lozenge, [data-test-id="issue.views.field.multi-select.labels"] span')
                issue['labels'] = [l.text for l in labels if l.text]
            except:
                pass
            
            issue['links'] = self.get_issue_links(issue_key)
            
        except Exception as e:
            print(f"Error getting issue details for {issue_key}: {e}")
        
        return issue
    
    def get_issue_links(self, issue_key: str) -> List[Dict]:
        """
        Extract issue links (blockers, dependencies).
        
        Args:
            issue_key: Issue key
            
        Returns:
            List of link dictionaries
        """
        links = []
        
        try:
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, '#linkingmodule .link-content, [data-test-id="issue.views.field.issuelinks"]')
            
            for elem in link_elements:
                try:
                    link_type = elem.find_element(By.CSS_SELECTOR, '.link-type, .css-1n7f8a4').text
                    linked_issue = elem.find_element(By.CSS_SELECTOR, '.link-issue-key a, [data-test-id="issue-link"]')
                    linked_key = linked_issue.text
                    
                    links.append({
                        'type': link_type,
                        'target': linked_key,
                        'direction': 'inward' if 'by' in link_type.lower() else 'outward'
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"Error getting issue links: {e}")
        
        return links
    
    def get_epic_children(self, epic_key: str) -> List[Dict]:
        """Get all issues under an epic"""
        jql = f'"Epic Link" = {epic_key} OR parent = {epic_key}'
        return self.execute_jql(jql)
    
    def get_sprint_issues(self, sprint_name: str) -> List[Dict]:
        """Get all issues in a sprint"""
        jql = f'sprint = "{sprint_name}"'
        return self.execute_jql(jql)
    
    def get_project_issues(self, project_key: str, issue_types: List[str] = None) -> List[Dict]:
        """Get issues from a project, optionally filtered by type"""
        jql = f'project = {project_key}'
        if issue_types:
            types = ', '.join(f'"{t}"' for t in issue_types)
            jql += f' AND type in ({types})'
        return self.execute_jql(jql)
    
    def check_authentication(self) -> bool:
        """Check if currently authenticated to Jira"""
        try:
            current_url = self.driver.current_url
            return 'login' not in current_url.lower() and 'auth' not in current_url.lower()
        except:
            return False
