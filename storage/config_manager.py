"""
Config Manager
YAML-based configuration management with schema validation
"""
import os
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime


class ConfigManager:
    """
    Manages Waypoint configuration stored in YAML.
    Provides validation, defaults, and change tracking.
    """
    
    DEFAULT_CONFIG = {
        'jira': {
            'base_url': '',
            'project_key': '',
            'session_persist_hours': 8
        },
        'github': {
            'organization': '',
            'repositories': [],
            'token': ''
        },
        'extensions': {},
        'schedule': {
            'enabled': False,
            'interval_minutes': 60,
            'lookback_hours': 24
        },
        'performance': {
            'delay_between_updates_seconds': 2,
            'max_concurrent_updates': 1
        },
        'logging': {
            'level': 'INFO',
            'file': 'waypoint.log'
        },
        'ui': {
            'theme': 'light',
            'default_persona': 'dashboard'
        },
        'insights': {
            'enabled': True,
            'rules': []
        }
    }
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self._config: Dict = {}
        self._last_modified: Optional[datetime] = None
        self.load()
    
    def load(self) -> Dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                self._last_modified = datetime.fromtimestamp(
                    os.path.getmtime(self.config_path)
                )
            else:
                self._config = {}
            
            self._apply_defaults()
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = {}
            self._apply_defaults()
        
        return self._config
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            self._last_modified = datetime.now()
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _apply_defaults(self):
        """Apply default values for missing keys"""
        self._config = self._merge_defaults(self.DEFAULT_CONFIG, self._config)
    
    def _merge_defaults(self, defaults: Dict, config: Dict) -> Dict:
        """Recursively merge defaults with config"""
        result = defaults.copy()
        
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_defaults(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., 'jira.base_url')
            default: Default value if key not found
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., 'jira.base_url')
            value: Value to set
            save: Whether to save immediately
        """
        keys = key.split('.')
        config = self._config
        
        try:
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            
            if save:
                return self.save()
            return True
            
        except Exception as e:
            print(f"Error setting config key {key}: {e}")
            return False
    
    def get_section(self, section: str) -> Dict:
        """Get entire configuration section"""
        return self._config.get(section, {})
    
    def set_section(self, section: str, data: Dict, save: bool = True) -> bool:
        """Set entire configuration section"""
        self._config[section] = data
        if save:
            return self.save()
        return True
    
    def get_all(self) -> Dict:
        """Get entire configuration"""
        return self._config.copy()
    
    def update(self, updates: Dict, save: bool = True) -> bool:
        """
        Update configuration with partial data.
        Merges with existing config.
        """
        self._config = self._merge_defaults(self._config, updates)
        if save:
            return self.save()
        return True
    
    def get_extension_config(self, extension_name: str) -> Dict:
        """Get configuration for a specific extension"""
        return self._config.get('extensions', {}).get(extension_name, {})
    
    def set_extension_config(self, extension_name: str, config: Dict, save: bool = True) -> bool:
        """Set configuration for a specific extension"""
        if 'extensions' not in self._config:
            self._config['extensions'] = {}
        
        self._config['extensions'][extension_name] = config
        
        if save:
            return self.save()
        return True
    
    def get_insight_rules(self) -> List[Dict]:
        """Get configured insight rules"""
        return self._config.get('insights', {}).get('rules', [])
    
    def add_insight_rule(self, rule: Dict, save: bool = True) -> bool:
        """Add a new insight rule"""
        if 'insights' not in self._config:
            self._config['insights'] = {'enabled': True, 'rules': []}
        
        if 'rules' not in self._config['insights']:
            self._config['insights']['rules'] = []
        
        self._config['insights']['rules'].append(rule)
        
        if save:
            return self.save()
        return True
    
    def remove_insight_rule(self, rule_name: str, save: bool = True) -> bool:
        """Remove an insight rule by name"""
        rules = self._config.get('insights', {}).get('rules', [])
        self._config['insights']['rules'] = [r for r in rules if r.get('name') != rule_name]
        
        if save:
            return self.save()
        return True
    
    def get_bulk_update_templates(self, extension: str = 'jira') -> List[Dict]:
        """Get bulk update templates for an extension"""
        ext_config = self.get_extension_config(extension)
        return ext_config.get('bulk_update_templates', [])
    
    def add_bulk_update_template(self, extension: str, template: Dict, save: bool = True) -> bool:
        """Add a bulk update template"""
        ext_config = self.get_extension_config(extension)
        
        if 'bulk_update_templates' not in ext_config:
            ext_config['bulk_update_templates'] = []
        
        ext_config['bulk_update_templates'].append(template)
        
        return self.set_extension_config(extension, ext_config, save)
    
    def validate(self) -> Dict:
        """
        Validate current configuration.
        
        Returns:
            {'valid': bool, 'errors': [...], 'warnings': [...]}
        """
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        if not self.get('jira.base_url'):
            result['warnings'].append('Jira base URL not configured')
        
        return result
    
    def reset_to_defaults(self, section: str = None, save: bool = True) -> bool:
        """Reset configuration to defaults"""
        if section:
            if section in self.DEFAULT_CONFIG:
                self._config[section] = self.DEFAULT_CONFIG[section].copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        
        if save:
            return self.save()
        return True
    
    def export_config(self) -> str:
        """Export configuration as YAML string"""
        return yaml.dump(self._config, default_flow_style=False, allow_unicode=True)
    
    def import_config(self, yaml_str: str, save: bool = True) -> bool:
        """Import configuration from YAML string"""
        try:
            new_config = yaml.safe_load(yaml_str)
            if isinstance(new_config, dict):
                self._config = new_config
                self._apply_defaults()
                if save:
                    return self.save()
                return True
            return False
        except Exception as e:
            print(f"Error importing config: {e}")
            return False


_config_instance: Optional[ConfigManager] = None


def get_config_manager(config_path: str = 'config.yaml') -> ConfigManager:
    """Get or create the global config manager instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance
