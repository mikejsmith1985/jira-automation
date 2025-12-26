"""
Waypoint Extension System
Base classes for all extensions (data sources and sinks)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class ExtensionCapability(Enum):
    """Capabilities an extension can provide"""
    READ = "read"
    WRITE = "write"
    BULK_UPDATE = "bulk_update"
    METRICS = "metrics"
    EXPORT = "export"


class ExtensionStatus(Enum):
    """Extension status states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


class BaseExtension(ABC):
    """
    Base class for all Waypoint extensions.
    Extensions provide pluggable data sources and sinks.
    """
    
    def __init__(self):
        self._status = ExtensionStatus.UNINITIALIZED
        self._last_error: Optional[str] = None
        self._config: Dict = {}
        self._initialized_at: Optional[datetime] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique extension identifier (e.g., 'jira', 'github')"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI (e.g., 'Jira (Selenium)')"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version (e.g., '1.0.0')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what the extension does"""
        pass
    
    @property
    @abstractmethod
    def config_schema(self) -> Dict:
        """
        JSON Schema for extension configuration.
        Used to generate UI forms and validate config.
        """
        pass
    
    @property
    def status(self) -> ExtensionStatus:
        """Current extension status"""
        return self._status
    
    @property
    def last_error(self) -> Optional[str]:
        """Last error message if status is ERROR"""
        return self._last_error
    
    @property
    def config(self) -> Dict:
        """Current configuration"""
        return self._config
    
    @abstractmethod
    def initialize(self, config: Dict, **kwargs) -> bool:
        """
        Initialize extension with configuration.
        
        Args:
            config: Configuration dictionary matching config_schema
            **kwargs: Additional initialization arguments (e.g., driver for Selenium)
            
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict:
        """
        Test if extension can connect to its data source.
        
        Returns:
            {
                'success': bool,
                'authenticated': bool (if applicable),
                'message': str,
                'details': dict (optional extra info)
            }
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[ExtensionCapability]:
        """Return list of capabilities this extension provides"""
        pass
    
    def get_status_info(self) -> Dict:
        """Get full status information"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'version': self.version,
            'status': self._status.value,
            'last_error': self._last_error,
            'initialized_at': self._initialized_at.isoformat() if self._initialized_at else None,
            'capabilities': [c.value for c in self.get_capabilities()]
        }
    
    def shutdown(self):
        """Clean shutdown of extension"""
        self._status = ExtensionStatus.UNINITIALIZED
        self._initialized_at = None


class DataSourceExtension(BaseExtension):
    """
    Extension that can read/extract data from an external source.
    Used for: Jira data extraction, GitHub PR fetching, CSV import
    """
    
    @abstractmethod
    def extract_data(self, query: Dict) -> Dict:
        """
        Extract data based on query parameters.
        
        Args:
            query: Query parameters (e.g., {'jql': '...', 'max_results': 500})
            
        Returns:
            {
                'success': bool,
                'data': Any (raw extracted data),
                'count': int,
                'query': dict (echo of query),
                'timestamp': str (ISO format),
                'error': str (if success=False)
            }
        """
        pass
    
    @abstractmethod
    def transform_to_features(self, raw_data: Any) -> List[Dict]:
        """
        Transform raw data to Waypoint feature structure.
        
        Args:
            raw_data: Data returned from extract_data()
            
        Returns:
            List of feature dictionaries:
            [
                {
                    'key': str,
                    'name': str,
                    'status': str,
                    'progress': float (0-100),
                    'assignee': str (optional),
                    'children': [...] (optional)
                }
            ]
        """
        pass
    
    @abstractmethod
    def transform_to_dependencies(self, raw_data: Any) -> Dict:
        """
        Transform raw data to dependency graph.
        
        Args:
            raw_data: Data returned from extract_data()
            
        Returns:
            Dependency dictionary:
            {
                'issue_key': {
                    'title': str,
                    'status': str,
                    'blockers': [{'key': str, 'title': str}],
                    'blocks': [{'key': str, 'title': str}]
                }
            }
        """
        pass
    
    def transform_to_metrics(self, raw_data: Any, mode: str = 'scrum') -> Dict:
        """
        Transform raw data to metrics structure.
        Override in subclass if metrics capability supported.
        
        Args:
            raw_data: Data returned from extract_data()
            mode: 'scrum' or 'kanban'
            
        Returns:
            Metrics dictionary
        """
        return {}


class DataSinkExtension(BaseExtension):
    """
    Extension that can write/update data to an external source.
    Used for: Jira ticket updates, GitHub PR comments
    """
    
    @abstractmethod
    def update_single(self, identifier: str, updates: Dict) -> Dict:
        """
        Update a single item.
        
        Args:
            identifier: Unique ID (e.g., 'PROJ-123' for Jira)
            updates: Dictionary of updates to apply
            
        Returns:
            {
                'success': bool,
                'identifier': str,
                'applied_updates': dict,
                'error': str (if success=False)
            }
        """
        pass
    
    @abstractmethod
    def update_bulk(self, query: Dict, updates: Dict) -> Dict:
        """
        Apply updates to all items matching query.
        
        Args:
            query: Query to find items (e.g., {'jql': '...'})
            updates: Updates to apply to each item
            
        Returns:
            {
                'success': bool,
                'total': int,
                'updated': int,
                'failed': int,
                'errors': [{'identifier': str, 'error': str}]
            }
        """
        pass
    
    def validate_updates(self, updates: Dict) -> Dict:
        """
        Validate updates before applying.
        Override for custom validation.
        
        Returns:
            {'valid': bool, 'errors': [...]}
        """
        return {'valid': True, 'errors': []}


class DualExtension(DataSourceExtension, DataSinkExtension):
    """
    Extension that provides both read and write capabilities.
    Most integrations (Jira, GitHub) are dual extensions.
    """
    pass
