"""
GitHub scraper module
Scrapes GitHub for Pull Request information when API is not available

WHAT THIS FILE DOES (Simple Explanation):
This file is like a spy that goes to GitHub and collects information about Pull Requests.
It looks at PR pages just like you would in a web browser, reads the information,
and brings it back to the main app.

WHY WE NEED IT:
- You don't have GitHub API access yet
- So we need to "scrape" (read) the web pages instead
- Later, when you get API access, we can replace this with API calls

HOW IT WORKS:
1. Opens GitHub in a Chrome browser (controlled by Selenium)
2. Goes to the Pull Requests page for a repository
3. Finds each PR on the page
4. Extracts: Title, URL, Author, Status (open/merged/closed)
5. Looks for Jira ticket keys in the PR title (like "ABC-123")
6. Returns all this info to the sync engine
"""
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GitHubScraper:
    """
    The GitHub spy/detective that collects PR information
    
    Think of this like a research assistant who:
    - Goes to GitHub
    - Makes a list of all the PRs
    - Writes down the important details
    - Brings the list back to you
    """
    
    def __init__(self, driver, config):
        """
        Initialize the scraper when it's first created
        
        Args:
            driver: The Chrome browser controller (our "steering wheel")
            config: Dictionary with settings from config.yaml
        """
        self.driver = driver  # The browser we'll use to visit GitHub
        self.config = config  # All our settings
        self.base_url = config['github']['base_url']  # Usually "https://github.com"
        self.org = config['github']['organization']  # Your company's GitHub org
        
    def get_recent_prs(self, repo_name, hours_back=24):
        """
        Get a list of recently updated Pull Requests from a repository
        
        This is like asking: "What PRs have been touched in the last 24 hours?"
        
        Args:
            repo_name: The repository to check (like "my-awesome-app")
            hours_back: How far back to look (default: 24 hours)
            
        Returns:
            A list of PR dictionaries, each containing:
            {
                'repo': 'my-repo',
                'number': '123',
                'title': 'ABC-123: Fix login bug',
                'url': 'https://github.com/org/repo/pull/123',
                'status': 'open',  # or 'merged' or 'closed'
                'author': 'john_doe',
                'branch': 'feature/ABC-123-fix-login',
                'ticket_keys': ['ABC-123']  # Jira tickets found in title
            }
        """
        # Build the URL to the Pull Requests page
        # Example: https://github.com/my-org/my-repo/pulls
        url = f"{self.base_url}/{self.org}/{repo_name}/pulls"
        
        try:
            # Step 1: Navigate to the PRs page
            self.driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            prs = []  # Empty list to store PRs we find
            
            # Step 2: Find all PR boxes on the page
            # GitHub shows PRs in divs with IDs like "issue_1", "issue_2", etc.
            pr_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[id^="issue_"]')
            
            # Step 3: Loop through each PR and extract its data
            for pr_elem in pr_elements[:20]:  # Only look at first 20 PRs
                try:
                    # Extract all the info from this PR
                    pr_data = self._extract_pr_data(pr_elem, repo_name)
                    
                    # Only add it to our list if we got valid data
                    if pr_data:
                        prs.append(pr_data)
                        
                except Exception as e:
                    # If we can't read one PR, skip it and continue
                    print(f"Error extracting PR: {e}")
                    continue
            
            # Return the list of all PRs we found
            return prs
            
        except Exception as e:
            # If something goes wrong, print error and return empty list
            print(f"Error getting PRs from {repo_name}: {e}")
            return []
    
    def _extract_pr_data(self, pr_elem, repo_name):
        """
        Extract data from a single PR element (private helper function)
        
        The underscore _ at the start means "this is a helper function, 
        not meant to be called from outside this class"
        
        Args:
            pr_elem: The HTML element containing PR info
            repo_name: The repository name
            
        Returns:
            Dictionary with PR data, or None if we can't extract it
        """
        try:
            # Step 1: Get the PR title and URL
            # Look for the main link (has class "Link--primary")
            title_elem = pr_elem.find_element(By.CSS_SELECTOR, 'a.Link--primary')
            title = title_elem.text  # Get the text
            pr_url = title_elem.get_attribute('href')  # Get the link
            
            # Step 2: Extract PR number from the URL
            # URL looks like: https://github.com/org/repo/pull/123
            # We want just the "123" part
            pr_number = pr_url.split('/')[-1]
            
            # Step 3: Find Jira ticket keys in the title
            # Example title: "ABC-123: Fix login bug"
            # Pattern looks for: LETTERS-NUMBERS (like ABC-123)
            pattern = self.config['ticket_keys']['pattern']
            ticket_keys = re.findall(pattern, title)
            
            # If no ticket keys found, this PR isn't linked to Jira
            # So we skip it by returning None
            if not ticket_keys:
                return None
            
            # Step 4: Figure out if PR is open, merged, or closed
            status = 'open'  # Start by assuming it's open
            try:
                # Look for status badges
                if pr_elem.find_elements(By.CSS_SELECTOR, '.State--merged'):
                    status = 'merged'  # Purple badge = merged
                elif pr_elem.find_elements(By.CSS_SELECTOR, '.State--closed'):
                    status = 'closed'  # Red badge = closed
            except:
                pass  # If we can't find status, just use 'open'
            
            # Step 5: Get the author's name
            author = ''
            try:
                # Look for the "opened by X" link
                author_elem = pr_elem.find_element(By.CSS_SELECTOR, '.opened-by a')
                author = author_elem.text
            except:
                pass  # If can't find author, leave empty
            
            # Step 6: Get the branch name
            # This might require visiting the PR page (slow), so we skip for now
            branch_name = self._get_branch_name(pr_url)
            
            # Step 7: Return all the data we collected
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
        """
        Get the branch name from a PR page
        
        NOTE: This requires navigating to the PR page, which is slow.
        For now, we just return empty string. In the future, we could:
        1. Visit the PR page
        2. Find the branch name element
        3. Extract the text
        
        Args:
            pr_url: The URL of the PR page
            
        Returns:
            Branch name as string (currently always returns empty)
        """
        try:
            # TODO: Implement branch name extraction
            # For now, just return empty string to keep things fast
            # We can add this later if needed
            return ''
        except:
            return ''
    
    def get_pr_details(self, pr_url):
        """
        Get detailed information about a specific PR
        
        This visits an individual PR page to get more details like:
        - Branch name
        - Latest commit message
        - Who merged it (if merged)
        
        Use this when you need more info than the list page provides.
        
        Args:
            pr_url: Full URL to the PR (like https://github.com/org/repo/pull/123)
            
        Returns:
            Dictionary with detailed PR info:
            {
                'url': 'https://github.com/...',
                'commits': [],  # List of commits (not implemented yet)
                'last_commit_message': 'Fixed the login bug',
                'merged_by': 'jane_doe',
                'branch_name': 'feature/ABC-123-fix-login'
            }
        """
        try:
            # Step 1: Navigate to the specific PR page
            self.driver.get(pr_url)
            time.sleep(2)  # Wait for page to load
            
            # Step 2: Create a dictionary to store what we find
            details = {
                'url': pr_url,
                'commits': [],  # TODO: Could extract commit list later
                'last_commit_message': '',
                'merged_by': '',
                'branch_name': '',
                'target_branch': ''  # NEW: Target branch (DEV, INT, etc.)
            }
            
            # Step 3: Try to find the source and target branch names
            try:
                # GitHub shows: "username wants to merge X commits into BASE from HEAD"
                # Look for the base branch element
                base_branch_elem = self.driver.find_element(By.CSS_SELECTOR, '.base-ref')
                details['target_branch'] = base_branch_elem.text.strip()
                
                # Also get the source branch (head)
                head_branch_elem = self.driver.find_element(By.CSS_SELECTOR, '.head-ref')
                details['branch_name'] = head_branch_elem.text.strip()
            except:
                # Fallback: try older selectors
                try:
                    branch_elem = self.driver.find_element(By.CSS_SELECTOR, 'span.css-truncate-target')
                    details['branch_name'] = branch_elem.text
                except:
                    pass  # If not found, leave empty
            
            # Step 4: Try to find the last commit message
            try:
                # Latest commit is usually the first link with class "Link--primary text-bold"
                commit_elem = self.driver.find_element(By.CSS_SELECTOR, 'a.Link--primary.text-bold')
                details['last_commit_message'] = commit_elem.text
            except:
                pass
            
            # Step 5: Try to find who merged it (if it's merged)
            try:
                # Merged by info is in the "merged" section, class "author"
                merged_elem = self.driver.find_element(By.CSS_SELECTOR, '.merged .author')
                details['merged_by'] = merged_elem.text
            except:
                pass  # Not merged, or couldn't find info
            
            # Return all the details we collected
            return details
            
        except Exception as e:
            print(f"Error getting PR details: {e}")
            return {}  # Return empty dictionary if something went wrong
