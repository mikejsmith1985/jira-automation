"""
Version checker module
Checks GitHub for new releases and downloads/applies updates
"""
import requests
import json
import logging
import os
import sys
import subprocess
import tempfile
from packaging import version
from datetime import datetime, timedelta

class VersionChecker:
    """Check for new versions on GitHub and apply updates"""
    
    def __init__(self, current_version='1.0.0', owner='mikejsmith1985', repo='jira-automation', token=None):
        self.current_version = current_version
        self.owner = owner
        self.repo = repo
        self.token = token
        self.cache = None
        self.cache_time = None
        self.cache_duration = timedelta(hours=1)
        self.logger = logging.getLogger(__name__)
        
        # Get current executable path
        if getattr(sys, 'frozen', False):
            self.current_exe = sys.executable
        else:
            self.current_exe = os.path.abspath(__file__)
        
        # Check if running from temp directory
        self.running_from_temp = self._is_running_from_temp()
    
    def _is_running_from_temp(self):
        """Check if executable is running from a temporary directory"""
        temp_paths = [
            tempfile.gettempdir().lower(),
            os.path.join(os.path.expanduser('~'), 'appdata', 'local', 'temp').lower(),
            'temp\\',
            '\\temp\\'
        ]
        
        exe_path_lower = self.current_exe.lower()
        return any(temp_path in exe_path_lower for temp_path in temp_paths)
    
    def check_for_update(self, use_cache=True):
        """
        Check GitHub for the latest release
        
        Args:
            use_cache: Use cached result if available (default: True)
            
        Returns:
            Dictionary with update info:
            {
                'available': bool,
                'current_version': str,
                'latest_version': str,
                'release_notes': str,
                'download_url': str,
                'published_at': str,
                'asset_name': str,
                'asset_size': int
            }
        """
        # Check cache first
        if use_cache and self.cache and self.cache_time:
            if datetime.now() - self.cache_time < self.cache_duration:
                self.logger.debug("Using cached update check result")
                return self.cache
        
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Jira-Automation-Updater'
            }
            
            if self.token:
                headers['Authorization'] = f'token {self.token}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 403:
                # Rate limit exceeded
                error_msg = "GitHub rate limit exceeded. "
                if self.token:
                    error_msg += "Your token may be invalid or expired."
                else:
                    error_msg += "Please add a GitHub token in Integrations > GitHub to increase rate limit (60/hour → 5000/hour)."
                
                result = {
                    'available': False,
                    'current_version': self.current_version,
                    'error': error_msg,
                    'rate_limited': True
                }
                self._update_cache(result)
                return result
            
            if response.status_code == 404:
                # No releases yet
                result = {
                    'available': False,
                    'current_version': self.current_version,
                    'error': 'No releases found'
                }
                self._update_cache(result)
                return result
            
            if response.status_code != 200:
                return {
                    'available': False,
                    'current_version': self.current_version,
                    'error': f'GitHub API returned status {response.status_code}'
                }
            
            release = response.json()
            
            # Parse versions
            latest_version = release['tag_name'].lstrip('v')
            current_version = self.current_version.lstrip('v')
            
            # Compare versions using packaging library
            is_newer = version.parse(latest_version) > version.parse(current_version)
            
            if not is_newer:
                result = {
                    'available': False,
                    'current_version': self.current_version,
                    'latest_version': release['tag_name']
                }
                self._update_cache(result)
                return result
            
            # Find Windows executable asset
            download_url = None
            asset_name = None
            asset_size = 0
            asset_url = None  # API URL for private repo downloads
            
            for asset in release.get('assets', []):
                if asset['name'].endswith('.exe') or 'windows' in asset['name'].lower():
                    # For private repos, use API URL (asset['url']) not browser_download_url
                    # API URL works with Authorization header, browser URL doesn't
                    asset_url = asset['url']  # API endpoint
                    download_url = asset['browser_download_url']  # Fallback for public repos
                    asset_name = asset['name']
                    asset_size = asset['size']
                    break
            
            if not download_url:
                # No Windows binary found, just provide release page URL
                download_url = release['html_url']
                asset_name = 'Release Page'
            
            result = {
                'available': True,
                'current_version': self.current_version,
                'latest_version': release['tag_name'],
                'release_notes': release.get('body', 'No release notes available'),
                'download_url': asset_url if asset_url and self.token else download_url,  # Use API URL if we have token
                'published_at': release.get('published_at', ''),
                'asset_name': asset_name,
                'asset_size': asset_size
            }
            
            self._update_cache(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return {
                'available': False,
                'current_version': self.current_version,
                'error': str(e)
            }
    
    def list_recent_releases(self, limit=10):
        """
        List recent releases for rollback/history
        
        Args:
            limit: Number of releases to return (default: 10)
            
        Returns:
            List of release info dictionaries
        """
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases?per_page={limit}"
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Jira-Automation-Updater'
            }
            
            if self.token:
                headers['Authorization'] = f'token {self.token}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {'error': f'GitHub API returned status {response.status_code}'}
            
            releases = response.json()
            result = []
            
            for release in releases:
                # Find Windows asset
                download_url = None
                for asset in release.get('assets', []):
                    if asset['name'].endswith('.exe') or 'windows' in asset['name'].lower():
                        download_url = asset['browser_download_url']
                        break
                
                if not download_url:
                    download_url = release['html_url']
                
                version_str = release['tag_name'].lstrip('v')
                current_str = self.current_version.lstrip('v')
                
                result.append({
                    'version': release['tag_name'],
                    'name': release.get('name', release['tag_name']),
                    'published_at': release.get('published_at', ''),
                    'release_notes': release.get('body', ''),
                    'download_url': download_url,
                    'is_current': version_str == current_str
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error listing releases: {e}")
            return {'error': str(e)}
    
    def _update_cache(self, result):
        """Update the cache with new result"""
        self.cache = result
        self.cache_time = datetime.now()
    
    def download_and_apply_update(self, download_url, progress_callback=None):
        """
        Download and apply an update
        
        Args:
            download_url: URL to download .exe from
            progress_callback: Optional function(bytes_downloaded, total_bytes, status_message)
        
        Returns:
            Dictionary with result:
            {
                'success': bool,
                'message': str,
                'error': str  # if failed
            }
        """
        try:
            # Check if running from temp directory
            if self.running_from_temp:
                return {
                    'success': False,
                    'error': 'Cannot update: Application is running from a temporary directory. Please SAVE the executable to a permanent location (e.g., Desktop or Program Files) and run it from there. Then try updating again.'
                }
            
            # Create temp directory for download
            temp_dir = tempfile.gettempdir()
            temp_exe = os.path.join(temp_dir, 'waypoint_update.exe')
            
            if progress_callback:
                progress_callback(0, 0, 'Downloading update...')
            
            # Download the file with progress tracking
            headers = {
                'User-Agent': 'Jira-Automation-Updater'
            }
            
            if self.token:
                # Always use token if available (private repo requirement)
                headers['Authorization'] = f'token {self.token}'
                
                # If using API URL (contains api.github.com), we MUST use Accept header
                if 'api.github.com' in download_url:
                    headers['Accept'] = 'application/octet-stream'
                    self.logger.info("Using API endpoint for private repo download")

            self.logger.info(f"Downloading from: {download_url}")
            self.logger.info(f"Using token: {'Yes' if self.token else 'No'}")
            self.logger.info(f"Headers: {list(headers.keys())}")
            
            response = requests.get(download_url, stream=True, timeout=60, headers=headers)
            
            self.logger.info(f"Response status: {response.status_code}")
            
            # Check for authentication errors
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Authentication failed (401). Your GitHub token may be invalid or expired. Please update it in Settings > Integrations > Feedback.'
                }
            
            if response.status_code == 403:
                # Rate limit or permissions issue
                rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
                if rate_limit_remaining == '0':
                    return {
                        'success': False,
                        'error': f'GitHub rate limit exceeded (403). Resets at {response.headers.get("X-RateLimit-Reset", "unknown")}. Try again later or add a token.'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Access forbidden (403). Your token may not have permission to access this private repository. Ensure the token has "repo" scope.'
                    }
            
            if response.status_code == 404:
                return {
                    'success': False,
                    'error': 'Release asset not found (404). This is a private repository - ensure your GitHub token is configured in Settings > Integrations > Feedback.'
                }
            
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size, f'Downloading... {downloaded // 1024}KB / {total_size // 1024}KB')
            
            if progress_callback:
                progress_callback(total_size, total_size, 'Download complete. Preparing to restart...')
            
            # Create update script (batch file on Windows)
            update_script = os.path.join(temp_dir, 'update_waypoint.bat')
            update_log = os.path.join(temp_dir, 'waypoint_update.log')
            
            with open(update_script, 'w') as f:
                f.write('@echo off\n')
                f.write(f':: Waypoint Auto-Updater\n')
                f.write(f':: Log file: {update_log}\n')
                f.write(f'echo [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Update started > "{update_log}"\n')
                f.write(f'echo Source: {temp_exe} >> "{update_log}"\n')
                f.write(f'echo Target: {self.current_exe} >> "{update_log}"\n')
                f.write(f'\n')
                f.write(f'echo Waiting for Waypoint to close...\n')
                f.write(f'echo Waiting 3 seconds... >> "{update_log}"\n')
                f.write(f'timeout /t 3 /nobreak >nul\n')
                f.write(f'\n')
                f.write(f'echo Applying update...\n')
                f.write(f'echo Copying new executable... >> "{update_log}"\n')
                f.write(f'copy /Y "{temp_exe}" "{self.current_exe}" >> "{update_log}" 2>&1\n')
                f.write(f'set COPY_ERROR=%errorlevel%\n')
                f.write(f'echo Copy exit code: %COPY_ERROR% >> "{update_log}"\n')
                f.write(f'\n')
                f.write(f'if %COPY_ERROR% neq 0 (\n')
                f.write(f'    echo ERROR: Update failed! Exit code: %COPY_ERROR% >> "{update_log}"\n')
                f.write(f'    echo Update failed! Check {update_log} for details.\n')
                f.write(f'    echo Press any key to exit...\n')
                f.write(f'    pause >nul\n')
                f.write(f'    exit /b %COPY_ERROR%\n')
                f.write(f')\n')
                f.write(f'\n')
                f.write(f'echo Update successful! >> "{update_log}"\n')
                f.write(f'echo Update complete! Restarting Waypoint...\n')
                f.write(f'timeout /t 1 /nobreak >nul\n')
                f.write(f'start "" "{self.current_exe}"\n')
                f.write(f'echo Application restarted >> "{update_log}"\n')
                f.write(f'\n')
                f.write(f':: Cleanup\n')
                f.write(f'del "{temp_exe}" 2>nul\n')
                f.write(f'echo [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Update complete >> "{update_log}"\n')
                f.write(f'del "%~f0" 2>nul\n')  # Delete the batch file itself
            
            # Start the update script - SHOW WINDOW for debugging
            # User can see what's happening
            subprocess.Popen(['cmd', '/c', update_script], 
                           creationflags=0,  # Show window!
                           close_fds=True)
            
            return {
                'success': True,
                'message': f'Update downloaded. Watch the console window that appears.\n\nIf update fails, check: {update_log}',
                'restart_required': True
            }
            
        except Exception as e:
            self.logger.error(f"Error downloading/applying update: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_version(self):
        """Get the current version string"""
        return self.current_version
