"""
Waypoint Extensions Package
Provides pluggable data sources and sinks
"""
from extensions.base_extension import (
    BaseExtension,
    DataSourceExtension,
    DataSinkExtension,
    DualExtension,
    ExtensionCapability,
    ExtensionStatus
)
from extensions.extension_manager import ExtensionManager, get_extension_manager

__all__ = [
    'BaseExtension',
    'DataSourceExtension', 
    'DataSinkExtension',
    'DualExtension',
    'ExtensionCapability',
    'ExtensionStatus',
    'ExtensionManager',
    'get_extension_manager'
]
