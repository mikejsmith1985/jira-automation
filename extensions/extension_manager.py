"""
Extension Manager
Handles loading, configuration, and lifecycle of all extensions
"""
import os
import yaml
import importlib
from typing import Dict, List, Optional, Type
from datetime import datetime
from extensions.base_extension import (
    BaseExtension, 
    DataSourceExtension, 
    DataSinkExtension,
    ExtensionStatus,
    ExtensionCapability
)


class ExtensionManager:
    """
    Central manager for all Waypoint extensions.
    Handles registration, configuration, and lifecycle.
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.extensions: Dict[str, BaseExtension] = {}
        self.extension_configs: Dict[str, Dict] = {}
        self._load_config()
    
    def _load_config(self):
        """Load extension configurations from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    self.extension_configs = config.get('extensions', {})
                    
                    # Backwards compatibility for flat config structure
                    if not self.extension_configs:
                        # Check for known extensions in root config
                        if 'jira' in config:
                            self.extension_configs['jira'] = config['jira']
                        if 'github' in config:
                            self.extension_configs['github'] = config['github']
        except Exception as e:
            print(f"Error loading extension config: {e}")
            self.extension_configs = {}
    
    def _save_config(self):
        """Save extension configurations to config file"""
        try:
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            
            config['extensions'] = self.extension_configs
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving extension config: {e}")
    
    def register_extension(self, extension: BaseExtension) -> bool:
        """
        Register an extension with the manager.
        
        Args:
            extension: Extension instance to register
            
        Returns:
            True if registration successful
        """
        try:
            name = extension.name
            self.extensions[name] = extension
            
            if name in self.extension_configs:
                extension.initialize(self.extension_configs[name])
            
            return True
        except Exception as e:
            print(f"Error registering extension {extension.name}: {e}")
            return False
    
    def unregister_extension(self, name: str) -> bool:
        """Unregister an extension"""
        if name in self.extensions:
            self.extensions[name].shutdown()
            del self.extensions[name]
            return True
        return False
    
    def get_extension(self, name: str) -> Optional[BaseExtension]:
        """Get extension by name"""
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[Dict]:
        """
        List all registered extensions with status.
        
        Returns:
            List of extension info dictionaries
        """
        result = []
        for name, ext in self.extensions.items():
            info = ext.get_status_info()
            info['enabled'] = self.extension_configs.get(name, {}).get('enabled', True)
            result.append(info)
        return result
    
    def configure_extension(self, name: str, config: Dict) -> Dict:
        """
        Update extension configuration.
        
        Args:
            name: Extension name
            config: New configuration
            
        Returns:
            {'success': bool, 'message': str}
        """
        if name not in self.extensions:
            return {'success': False, 'message': f'Extension {name} not found'}
        
        try:
            extension = self.extensions[name]
            
            self.extension_configs[name] = config
            self._save_config()
            
            if config.get('enabled', True):
                success = extension.initialize(config)
                if success:
                    return {'success': True, 'message': 'Configuration saved and applied'}
                else:
                    return {'success': False, 'message': 'Configuration saved but initialization failed'}
            else:
                extension.shutdown()
                return {'success': True, 'message': 'Extension disabled'}
                
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_extension_config(self, name: str) -> Dict:
        """Get current configuration for extension"""
        return self.extension_configs.get(name, {})
    
    def get_extension_schema(self, name: str) -> Dict:
        """Get configuration schema for extension"""
        ext = self.extensions.get(name)
        if ext:
            return ext.config_schema
        return {}
    
    def test_extension(self, name: str) -> Dict:
        """Test extension connection"""
        ext = self.extensions.get(name)
        if not ext:
            return {'success': False, 'message': f'Extension {name} not found'}
        
        if ext.status != ExtensionStatus.READY:
            return {'success': False, 'message': 'Extension not initialized'}
        
        return ext.test_connection()
    
    def get_data_sources(self) -> List[DataSourceExtension]:
        """Get all extensions that can read data"""
        return [
            ext for ext in self.extensions.values()
            if isinstance(ext, DataSourceExtension) and ext.status == ExtensionStatus.READY
        ]
    
    def get_data_sinks(self) -> List[DataSinkExtension]:
        """Get all extensions that can write data"""
        return [
            ext for ext in self.extensions.values()
            if isinstance(ext, DataSinkExtension) and ext.status == ExtensionStatus.READY
        ]
    
    def get_extensions_with_capability(self, capability: ExtensionCapability) -> List[BaseExtension]:
        """Get all extensions that have a specific capability"""
        return [
            ext for ext in self.extensions.values()
            if capability in ext.get_capabilities() and ext.status == ExtensionStatus.READY
        ]
    
    def initialize_extension(self, name: str, **kwargs) -> Dict:
        """
        Initialize a specific extension with additional arguments.
        
        Args:
            name: Extension name
            **kwargs: Additional init arguments (e.g., driver for Selenium)
            
        Returns:
            {'success': bool, 'message': str}
        """
        ext = self.extensions.get(name)
        if not ext:
            return {'success': False, 'message': f'Extension {name} not found'}
        
        try:
            config = self.extension_configs.get(name, {})
            success = ext.initialize(config, **kwargs)
            
            if success:
                return {'success': True, 'message': f'{name} initialized successfully'}
            else:
                return {'success': False, 'message': f'{name} initialization failed'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def shutdown_all(self):
        """Shutdown all extensions gracefully"""
        for ext in self.extensions.values():
            try:
                ext.shutdown()
            except:
                pass


_manager_instance: Optional[ExtensionManager] = None


def get_extension_manager(config_path: str = 'config.yaml') -> ExtensionManager:
    """Get or create the global extension manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ExtensionManager(config_path)
    return _manager_instance
