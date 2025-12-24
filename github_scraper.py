"""
GitHub scraper module
Scrapes GitHub for PR information when API is not available
"""
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GitHubScraper:
    """Scrapes GitHub for PR data"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.base_url = config['github']['base_url']
        self.org = config['github']['organization']
        
    def get_recent_prs(self, repo_name, hours_back=24):
        """Get recently updated PRs from a repository"""
        url = f"{self.base_url}/{self.org}/{repo_name}/pulls"
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            prs = []
            # Find PR elements - adjust selectors based on GitHub's structure
            pr_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[id^="issue_"]')
            
            for pr_elem in pr_elements[:20]:  # Limit to 20 PRs
                try:
                    # Extract PR data
                    pr_data = self._extract_pr_data(pr_elem, repo_name)
                    if pr_data:
                        prs.append(pr_data)
                except Exception as e:
                    print(f"Error extracting PR: {e}")
                    continue
                    
            return prs
        except Exception as e:
            print(f"Error getting PRs from {repo_name}: {e}")
            return []
    
    def _extract_pr_data(self, pr_elem, repo_name):
        """Extract data from a single PR element"""
        try:
            # Get PR title and extract ticket keys
            title_elem = pr_elem.find_element(By.CSS_SELECTOR, 'a.Link--primary')
            title = title_elem.text
            pr_url = title_elem.get_attribute('href')
            
            # Extract PR number from URL
            pr_number = pr_url.split('/')[-1]
            
            # Extract ticket keys from title
            pattern = self.config['ticket_keys']['pattern']
            ticket_keys = re.findall(pattern, title)
            
            if not ticket_keys:
                return None
            
            # Get PR status (open, merged, closed)
            status = 'open'
            try:
                if pr_elem.find_elements(By.CSS_SELECTOR, '.State--merged'):
                    status = 'merged'
                elif pr_elem.find_elements(By.CSS_SELECTOR, '.State--closed'):
                    status = 'closed'
            except:
                pass
            
            # Get author
            author = ''
            try:
                author_elem = pr_elem.find_element(By.CSS_SELECTOR, '.opened-by a')
                author = author_elem.text
            except:
                pass
            
            # Get branch name (may need to navigate to PR page)
            branch_name = self._get_branch_name(pr_url)
            
            return {
                'repo': repo_name,
                'number': pr_number,
                'title': title,
                'url': pr_url,
                'status': status,
                'author': author,
                'branch': branch_name,
                'ticket_keys': ticket_keys
            }
        except Exception as e:
            print(f"Error extracting PR data: {e}")
            return None
    
    def _get_branch_name(self, pr_url):
        """Get branch name from PR page"""
        try:
            # This might require navigating to the PR page
            # For now, extract from URL or return empty
            # TODO: Navigate to PR page and scrape branch name
            return ''
        except:
            return ''
    
    def get_pr_details(self, pr_url):
        """Get detailed information about a specific PR"""
        try:
            self.driver.get(pr_url)
            time.sleep(2)
            
            details = {
                'url': pr_url,
                'commits': [],
                'last_commit_message': '',
                'merged_by': '',
                'branch_name': ''
            }
            
            # Get branch name
            try:
                branch_elem = self.driver.find_element(By.CSS_SELECTOR, 'span.css-truncate-target')
                details['branch_name'] = branch_elem.text
            except:
                pass
            
            # Get last commit message
            try:
                commit_elem = self.driver.find_element(By.CSS_SELECTOR, 'a.Link--primary.text-bold')
                details['last_commit_message'] = commit_elem.text
            except:
                pass
            
            # Get merged by (if merged)
            try:
                merged_elem = self.driver.find_element(By.CSS_SELECTOR, '.merged .author')
                details['merged_by'] = merged_elem.text
            except:
                pass
            
            return details
        except Exception as e:
            print(f"Error getting PR details: {e}")
            return {}
