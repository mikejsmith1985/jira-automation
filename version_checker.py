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
            
            # Find downloadable asset (prefer ZIP for v2.0+, fallback to EXE for v1.x)
            download_url = None
            asset_name = None
            asset_size = 0
            asset_url = None  # API URL for private repo downloads
            
            # First, look for ZIP file (v2.0+ folder-based distribution)
            for asset in release.get('assets', []):
                if asset['name'].lower().endswith('.zip'):
                    asset_url = asset['url']
                    download_url = asset['browser_download_url']
                    asset_name = asset['name']
                    asset_size = asset['size']
                    self.logger.info(f"Found ZIP asset: {asset_name} (v2.0+ folder-based)")
                    break
            
            # Fallback to EXE (legacy v1.x)
            if not download_url:
                for asset in release.get('assets', []):
                    if asset['name'].endswith('.exe') or 'windows' in asset['name'].lower():
                        asset_url = asset['url']
                        download_url = asset['browser_download_url']
                        asset_name = asset['name']
                        asset_size = asset['size']
                        self.logger.info(f"Found EXE asset: {asset_name} (v1.x legacy)")
                        break
            
            if not download_url:
                # No binary found, just provide release page URL
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
        Download and apply an update using Forge-Terminal pattern (simple & reliable)
        
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
            
            # Download to temp file
            temp_dir = tempfile.gettempdir()
            temp_exe = os.path.join(temp_dir, 'waypoint_update.exe')
            
            # Build request headers
            headers = {
                'Accept': 'application/octet-stream',
                'User-Agent': 'Waypoint-Updater'
            }
            
            if self.token:
                if download_url.startswith('https://api.github.com'):
                    headers['Authorization'] = f'token {self.token}'
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
                progress_callback(total_size, total_size, 'Download complete. Applying update...')
            
            # Apply update using Forge-Terminal pattern (simple file operations)
            result = self.apply_update_forge_pattern(temp_exe)
            
            if result['success'] and progress_callback:
                progress_callback(total_size, total_size, 'Update applied! Please restart Waypoint.')
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error downloading/applying update: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_update_forge_pattern(self, temp_exe):
        """
        Apply update using Forge-Terminal pattern (simple & reliable)
        
        Forge-Terminal approach (Go):
            oldPath := currentPath + ".old"
            os.Remove(oldPath)                     // Remove old backup
            os.Rename(currentPath, oldPath)         // Backup current
            copyFile(newBinaryPath, currentPath)    // Install new
            os.Remove(newBinaryPath)                // Cleanup temp
        
        This is MUCH simpler than batch scripts and works reliably.
        """
        try:
            current_exe = self.current_exe
            backup_exe = current_exe + '.old'
            
            self.logger.info(f"[Forge Pattern] Applying update...")
            self.logger.info(f"  Current: {current_exe}")
            self.logger.info(f"  Backup:  {backup_exe}")
            self.logger.info(f"  New:     {temp_exe}")
            
            # Step 1: Remove old backup if exists
            if os.path.exists(backup_exe):
                self.logger.info(f"[Forge Pattern] Removing old backup...")
                try:
                    os.remove(backup_exe)
                except Exception as e:
                    self.logger.warning(f"Could not remove old backup: {e}")
                    # Not critical, continue
            
            # Step 2: Rename current to backup
            self.logger.info(f"[Forge Pattern] Backing up current executable...")
            os.rename(current_exe, backup_exe)
            
            # Step 3: Copy new binary to current location
            self.logger.info(f"[Forge Pattern] Installing new version...")
            import shutil
            shutil.copy2(temp_exe, current_exe)
            
            # Step 4: Cleanup temp file
            self.logger.info(f"[Forge Pattern] Cleaning up temp file...")
            os.remove(temp_exe)
            
            self.logger.info(f"[Forge Pattern] ✅ Update applied successfully!")
            
            return {
                'success': True,
                'message': 'Update applied successfully! Please close and restart Waypoint to use the new version.',
                'restart_required': True,
                'backup_location': backup_exe
            }
            
        except Exception as e:
            self.logger.error(f"[Forge Pattern] ❌ Update failed: {e}")
            
            # Try to restore backup if we renamed but failed to copy
            if not os.path.exists(current_exe) and os.path.exists(backup_exe):
                try:
                    self.logger.info(f"[Forge Pattern] Restoring backup...")
                    os.rename(backup_exe, current_exe)
                    self.logger.info(f"[Forge Pattern] Backup restored")
                except Exception as restore_err:
                    self.logger.error(f"[Forge Pattern] Failed to restore backup: {restore_err}")
            
            return {
                'success': False,
                'error': f'Update failed: {str(e)}. If Waypoint won\'t start, rename {backup_exe} to {current_exe}'
            }
    def get_current_version(self):
        """Get the current version string"""
        return self.current_version
