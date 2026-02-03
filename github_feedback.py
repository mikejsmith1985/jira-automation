"""
GitHub Feedback Integration
Submits bug reports and feedback as GitHub issues with attachments
"""
import os
import json
import base64
import tempfile
from datetime import datetime
from github import Github, GithubException
from pathlib import Path


class GitHubFeedback:
    """Manages feedback submission to GitHub issues"""
    
    def __init__(self, token=None, repo_name=None):
        """
        Initialize GitHub feedback client
        
        Args:
            token: GitHub personal access token
            repo_name: Repository name in format 'owner/repo'
        """
        self.token = token
        self.repo_name = repo_name
        self.client = None
        self.repo = None
    
    def _connect(self):
        """Establish connection to GitHub"""
        try:
            self.client = Github(self.token)
            self.repo = self.client.get_repo(self.repo_name)
            return True
        except GithubException as e:
            return False
        except Exception as e:
            return False
    
    def validate_token(self):
        """
        Validate GitHub token and repository access
        
        Returns:
            dict: {'valid': bool, 'user': str, 'error': str}
        """
        try:
            if not self.client:
                if not self._connect():
                    return {
                        'valid': False,
                        'user': None,
                        'error': 'Failed to connect to GitHub. Check token and repo name.'
                    }
            
            user = self.client.get_user()
            return {
                'valid': True,
                'user': user.login,
                'error': None
            }
        except Exception as e:
            return {
                'valid': False,
                'user': None,
                'error': str(e)
            }
    
    def create_issue(self, title, body, labels=None, attachments=None):
        """
        Create a new GitHub issue with attachments
        
        Args:
            title: Issue title
            body: Issue description
            labels: List of label names
            attachments: List of dicts with 'name', 'content' (base64), 'mime_type'
        
        Returns:
            dict: {'success': bool, 'issue_url': str, 'issue_number': int, 'error': str}
        """
        try:
            if not self.repo:
                self._connect()
            
            # GitHub issue body has ~65KB limit - don't embed large attachments
            # Instead, save to temp and upload as issue comments
            full_body = body
            
            # Create the issue first (without large attachments)
            issue_labels = labels or ['bug', 'user-feedback']
            issue = self.repo.create_issue(
                title=title,
                body=full_body,
                labels=issue_labels
            )
            
            # Upload attachments as comments if present
            if attachments:
                for attachment in attachments:
                    name = attachment.get('name', 'attachment')
                    content = attachment.get('content')  # base64 encoded
                    mime_type = attachment.get('mime_type', 'application/octet-stream')
                    
                    try:
                        # Decode base64 back to binary
                        import base64
                        file_data = base64.b64decode(content)
                        
                        # For images, embed in comment (GitHub supports this)
                        if mime_type.startswith('image/') and len(file_data) < 10_000_000:  # 10MB limit
                            # GitHub does NOT support data URLs in comments!
                            # GitHub comment limit is 65536 chars, base64 images exceed this
                            # Just note the attachment - user can describe what they saw
                            size_kb = len(file_data) / 1024
                            comment_body = f"### {name}\n\n"
                            comment_body += f"**Type:** {mime_type}\n"
                            comment_body += f"**Size:** {size_kb:.1f} KB\n\n"
                            comment_body += "*Screenshot captured during feedback. GitHub API does not support direct image upload to issue comments.*\n"
                            comment_body += "*Tip: Manually drag-and-drop the screenshot to add it, or describe the issue in the body.*"
                            
                            issue.create_comment(comment_body)
                        else:
                            # For videos/large files, just note them
                            size_mb = len(file_data) / (1024 * 1024)
                            comment_body = f"### {name}\n\n"
                            comment_body += f"**Type:** {mime_type}\n"
                            comment_body += f"**Size:** {size_mb:.2f} MB\n\n"
                            comment_body += "*Note: File too large to embed directly. Original file captured during feedback submission.*"
                            issue.create_comment(comment_body)
                    except Exception as attach_error:
                        # If attachment fails, add a comment noting the failure
                        issue.create_comment(f"⚠️ Failed to attach {name}: {str(attach_error)}")
            
            return {
                'success': True,
                'issue_url': issue.html_url,
                'issue_number': issue.number,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'issue_url': None,
                'issue_number': None,
                'error': str(e)
            }
    
    def get_user_issues(self, username, limit=10):
        """
        Get recent issues created by a specific user
        
        Args:
            username: GitHub username
            limit: Maximum number of issues to return
        
        Returns:
            list: List of issue dicts with title, number, url, state
        """
        try:
            if not self.repo:
                self._connect()
            
            issues = self.repo.get_issues(
                creator=username,
                state='all',
                sort='created',
                direction='desc'
            )
            
            result = []
            for issue in issues[:limit]:
                result.append({
                    'number': issue.number,
                    'title': issue.title,
                    'url': issue.html_url,
                    'state': issue.state,
                    'created_at': issue.created_at.isoformat(),
                    'labels': [label.name for label in issue.labels]
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to fetch issues: {str(e)}")
    
    def download_issue_image(self, image_url):
        """
        Download an image from a GitHub issue to temp directory
        
        Args:
            image_url: URL of the image
        
        Returns:
            str: Path to downloaded image in temp directory
        """
        try:
            import requests
            
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Create temp file
            suffix = Path(image_url).suffix or '.png'
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix='gh_issue_img_'
            )
            
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            raise Exception(f"Failed to download image: {str(e)}")


class LogCapture:
    """Captures and aggregates logs for feedback submission"""
    
    def __init__(self, log_file='jira-sync.log'):
        """
        Initialize log capture
        
        Args:
            log_file: Path to application log file
        """
        self.log_file = log_file
        self.console_logs = []
        self.network_errors = []
    
    def capture_recent_logs(self, minutes=5):
        """
        Capture logs from the last N minutes
        
        Args:
            minutes: Number of minutes to look back
        
        Returns:
            str: Formatted log output
        """
        try:
            if not os.path.exists(self.log_file):
                return "No log file found"
            
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            recent_logs = []
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    # Try to parse timestamp from log line
                    try:
                        # Support multiple log formats:
                        # Format 1: [YYYY-MM-DD HH:MM:SS] ...
                        # Format 2: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - ...
                        timestamp_str = None
                        log_time = None
                        
                        if line.startswith('['):
                            # Format 1: [2026-01-16 13:18:24]
                            timestamp_str = line[1:20]
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        elif len(line) >= 23 and line[4] == '-' and line[7] == '-' and line[10] == ' ':
                            # Format 2: 2026-01-16 13:18:24,746 - INFO -
                            timestamp_str = line[:19]  # YYYY-MM-DD HH:MM:SS
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if log_time and log_time >= cutoff_time:
                            recent_logs.append(line.strip())
                    except:
                        # If can't parse timestamp, include anyway if we're capturing
                        if recent_logs:
                            recent_logs.append(line.strip())
            
            return '\n'.join(recent_logs[-200:])  # Last 200 lines max
            
        except Exception as e:
            return f"Error capturing logs: {str(e)}"
    
    def add_console_log(self, log_entry):
        """
        Add a browser console log entry
        
        Args:
            log_entry: Dict with level, message, timestamp
        """
        self.console_logs.append(log_entry)
    
    def add_network_error(self, error_entry):
        """
        Add a network error entry
        
        Args:
            error_entry: Dict with url, status, error, timestamp
        """
        self.network_errors.append(error_entry)
    
    def get_console_logs(self, limit=100):
        """
        Get recent console logs
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            list: Recent console log entries
        """
        return self.console_logs[-limit:]
    
    def get_network_errors(self, limit=50):
        """
        Get recent network errors
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            list: Recent network error entries
        """
        return self.network_errors[-limit:]
    
    def export_all_logs(self):
        """
        Export all captured logs as formatted text
        
        Returns:
            str: Formatted log output for GitHub issue
        """
        output = []
        
        # Application logs
        output.append("## Application Logs\n")
        output.append("```")
        output.append(self.capture_recent_logs(minutes=5))
        output.append("```\n")
        
        # Console logs
        if self.console_logs:
            output.append("## Browser Console Logs\n")
            output.append("```javascript")
            for log in self.get_console_logs():
                timestamp = log.get('timestamp', 'unknown')
                level = log.get('level', 'log')
                message = log.get('message', '')
                output.append(f"[{timestamp}] {level.upper()}: {message}")
            output.append("```\n")
        
        # Network errors
        if self.network_errors:
            output.append("## Network Errors\n")
            output.append("```")
            for error in self.get_network_errors():
                timestamp = error.get('timestamp', 'unknown')
                url = error.get('url', '')
                status = error.get('status', 'unknown')
                error_msg = error.get('error', '')
                output.append(f"[{timestamp}] {url} - Status: {status}")
                output.append(f"  Error: {error_msg}")
            output.append("```\n")
        
        return '\n'.join(output)
