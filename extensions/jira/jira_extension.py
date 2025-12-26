"""
Jira Extension
Main entry point for Jira integration via Selenium
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from extensions.base_extension import (
    DualExtension,
    ExtensionCapability,
    ExtensionStatus
)
from extensions.jira.jira_scraper import JiraScraper
from extensions.jira.jira_updater import JiraUpdater
from extensions.jira.jira_transformer import JiraTransformer


class JiraExtension(DualExtension):
    """
    Main Jira extension providing read and write capabilities.
    Uses Selenium WebDriver for all Jira interactions.
    """
    
    @property
    def name(self) -> str:
        return "jira"
    
    @property
    def display_name(self) -> str:
        return "Jira (Selenium)"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Extract and update Jira data via Selenium browser automation"
    
    @property
    def config_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "title": "Jira Base URL",
                    "description": "Your Jira instance URL (e.g., https://company.atlassian.net)",
                    "format": "uri"
                },
                "project_key": {
                    "type": "string",
                    "title": "Default Project Key",
                    "description": "Default project for queries (e.g., MYPROJ)"
                },
                "session_persist_hours": {
                    "type": "integer",
                    "title": "Session Duration (hours)",
                    "description": "How long to persist login session",
                    "default": 8,
                    "minimum": 1,
                    "maximum": 24
                },
                "wait_timeout": {
                    "type": "integer",
                    "title": "Element Wait Timeout (seconds)",
                    "description": "How long to wait for page elements",
                    "default": 10,
                    "minimum": 5,
                    "maximum": 60
                },
                "default_jql": {
                    "type": "string",
                    "title": "Default JQL Query",
                    "description": "Default query for imports"
                },
                "field_mappings": {
                    "type": "object",
                    "title": "Custom Field Mappings",
                    "description": "Map custom field IDs to names",
                    "additionalProperties": {"type": "string"},
                    "default": {}
                },
                "bulk_update_templates": {
                    "type": "array",
                    "title": "Bulk Update Templates",
                    "description": "Predefined bulk update actions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "title": "Template Name"
                            },
                            "description": {
                                "type": "string",
                                "title": "Description"
                            },
                            "jql": {
                                "type": "string",
                                "title": "JQL Query"
                            },
                            "updates": {
                                "type": "object",
                                "title": "Updates to Apply",
                                "properties": {
                                    "status": {"type": "string"},
                                    "labels": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "comment": {"type": "string"},
                                    "assignee": {"type": "string"}
                                }
                            }
                        },
                        "required": ["name", "jql", "updates"]
                    },
                    "default": []
                },
                "auto_refresh_minutes": {
                    "type": "integer",
                    "title": "Auto-refresh Interval (minutes)",
                    "description": "Automatically refresh data (0 to disable)",
                    "default": 0,
                    "minimum": 0
                }
            },
            "required": ["base_url"]
        }
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.scraper: Optional[JiraScraper] = None
        self.updater: Optional[JiraUpdater] = None
        self.transformer = JiraTransformer()
        self._last_import: Optional[Dict] = None
    
    def initialize(self, config: Dict, **kwargs) -> bool:
        """
        Initialize the Jira extension.
        
        Args:
            config: Extension configuration
            driver: Selenium WebDriver instance (required)
        """
        try:
            self._status = ExtensionStatus.INITIALIZING
            self._config = config
            
            self.driver = kwargs.get('driver')
            
            if not self.driver:
                self._status = ExtensionStatus.ERROR
                self._last_error = "WebDriver not provided"
                return False
            
            if not config.get('base_url'):
                self._status = ExtensionStatus.ERROR
                self._last_error = "base_url is required"
                return False
            
            self.scraper = JiraScraper(self.driver, config)
            self.updater = JiraUpdater(self.driver, config, self.scraper)
            
            self._status = ExtensionStatus.READY
            self._initialized_at = datetime.now()
            self._last_error = None
            
            return True
            
        except Exception as e:
            self._status = ExtensionStatus.ERROR
            self._last_error = str(e)
            return False
    
    def test_connection(self) -> Dict:
        """Test connection to Jira"""
        if not self.driver:
            return {
                'success': False,
                'authenticated': False,
                'message': 'WebDriver not initialized'
            }
        
        try:
            base_url = self._config.get('base_url', '')
            self.driver.get(base_url)
            
            import time
            time.sleep(2)
            
            current_url = self.driver.current_url
            is_authenticated = 'login' not in current_url.lower() and 'auth' not in current_url.lower()
            
            return {
                'success': True,
                'authenticated': is_authenticated,
                'message': 'Connected to Jira' if is_authenticated else 'Please log in to Jira',
                'current_url': current_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'authenticated': False,
                'message': str(e)
            }
    
    def get_capabilities(self) -> List[ExtensionCapability]:
        """Return Jira extension capabilities"""
        return [
            ExtensionCapability.READ,
            ExtensionCapability.WRITE,
            ExtensionCapability.BULK_UPDATE,
            ExtensionCapability.METRICS,
            ExtensionCapability.EXPORT
        ]
    
    def extract_data(self, query: Dict) -> Dict:
        """
        Extract data from Jira.
        
        Args:
            query: {
                'jql': str (JQL query),
                'max_results': int (optional, default 500),
                'include_details': bool (optional, fetch full details)
            }
        """
        if not self.scraper:
            return {
                'success': False,
                'error': 'Scraper not initialized'
            }
        
        try:
            jql = query.get('jql', f'project = {self._config.get("project_key", "PROJ")}')
            max_results = query.get('max_results', 500)
            include_details = query.get('include_details', False)
            
            issues = self.scraper.execute_jql(jql, max_results)
            
            if include_details:
                detailed_issues = []
                for issue in issues[:50]:
                    details = self.scraper.get_issue_details(issue['key'])
                    detailed_issues.append(details)
                issues = detailed_issues
            
            self._last_import = {
                'timestamp': datetime.now().isoformat(),
                'query': jql,
                'count': len(issues),
                'data': issues
            }
            
            return {
                'success': True,
                'data': issues,
                'count': len(issues),
                'query': jql,
                'timestamp': self._last_import['timestamp']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def transform_to_features(self, raw_data: Any) -> List[Dict]:
        """Transform Jira issues to feature structure"""
        if isinstance(raw_data, dict):
            issues = raw_data.get('data', [])
        else:
            issues = raw_data
        
        return self.transformer.to_feature_structure(issues)
    
    def transform_to_dependencies(self, raw_data: Any) -> Dict:
        """Transform Jira issues to dependency graph"""
        if isinstance(raw_data, dict):
            issues = raw_data.get('data', [])
        else:
            issues = raw_data
        
        return self.transformer.to_dependency_graph(issues)
    
    def transform_to_metrics(self, raw_data: Any, mode: str = 'scrum') -> Dict:
        """Transform Jira issues to metrics"""
        if isinstance(raw_data, dict):
            issues = raw_data.get('data', [])
        else:
            issues = raw_data
        
        return self.transformer.to_metrics(issues, mode)
    
    def update_single(self, identifier: str, updates: Dict) -> Dict:
        """Update a single Jira issue"""
        if not self.updater:
            return {
                'success': False,
                'error': 'Updater not initialized'
            }
        
        return self.updater.update_issue(identifier, updates)
    
    def update_bulk(self, query: Dict, updates: Dict) -> Dict:
        """Bulk update Jira issues"""
        if not self.updater:
            return {
                'success': False,
                'error': 'Updater not initialized'
            }
        
        jql = query.get('jql', '')
        delay = query.get('delay_between', 1.0)
        
        return self.updater.bulk_update(jql, updates, delay)
    
    def get_bulk_update_templates(self) -> List[Dict]:
        """Get configured bulk update templates"""
        return self._config.get('bulk_update_templates', [])
    
    def execute_bulk_template(self, template_name: str) -> Dict:
        """Execute a predefined bulk update template"""
        templates = self.get_bulk_update_templates()
        
        template = next((t for t in templates if t['name'] == template_name), None)
        
        if not template:
            return {
                'success': False,
                'error': f'Template "{template_name}" not found'
            }
        
        return self.update_bulk(
            {'jql': template['jql']},
            template['updates']
        )
    
    def generate_daily_scrum_report(self, jql: str = None, insights: List[Dict] = None) -> Dict:
        """Generate daily scrum report"""
        if not self.scraper:
            return {'success': False, 'error': 'Scraper not initialized'}
        
        jql = jql or self._config.get('default_jql', f'project = {self._config.get("project_key")}')
        
        issues = self.scraper.execute_jql(jql)
        
        return {
            'success': True,
            'report': self.transformer.to_daily_scrum_report(issues, insights)
        }
    
    def export_to_csv(self, issues: List[Dict] = None, columns: List[str] = None) -> str:
        """Export issues to CSV"""
        if issues is None and self._last_import:
            issues = self._last_import.get('data', [])
        
        if not issues:
            return ''
        
        return self.transformer.to_csv(issues, columns)
    
    def import_from_csv(self, csv_data: str, mapping: Dict = None) -> List[Dict]:
        """Import issues from CSV"""
        return self.transformer.from_csv(csv_data, mapping)
    
    def get_last_import(self) -> Optional[Dict]:
        """Get last import metadata"""
        return self._last_import
    
    def shutdown(self):
        """Shutdown the extension"""
        self.scraper = None
        self.updater = None
        super().shutdown()
