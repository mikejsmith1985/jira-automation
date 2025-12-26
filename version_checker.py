"""
Version checker module
Checks GitHub for new releases and notifies users
"""
import requests
import json
import logging
from packaging import version
from datetime import datetime, timedelta

class VersionChecker:
    """Check for new versions on GitHub"""
    
    def __init__(self, current_version='1.0.0', owner='mikejsmith1985', repo='jira-automation'):
        self.current_version = current_version
        self.owner = owner
        self.repo = repo
        self.cache = None
        self.cache_time = None
        self.cache_duration = timedelta(hours=1)
        self.logger = logging.getLogger(__name__)
    
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
            
            response = requests.get(url, headers=headers, timeout=10)
            
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
            
            for asset in release.get('assets', []):
                if asset['name'].endswith('.exe') or 'windows' in asset['name'].lower():
                    download_url = asset['browser_download_url']
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
                'download_url': download_url,
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
    
    def get_current_version(self):
        """Get the current version string"""
        return self.current_version
