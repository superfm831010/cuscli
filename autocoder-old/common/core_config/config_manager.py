"""
Configuration management functionality.

This module provides configuration management methods including
basic configuration, batch operations, and nested configuration support.
"""

from typing import Dict, Any, List
from .base_manager import BaseMemoryManager


class ConfigManagerMixin:
    """Mixin class providing configuration management functionality."""
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._memory.conf.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        self._memory.conf[key] = value
        self.save_memory()
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration value."""
        if key in self._memory.conf:
            del self._memory.conf[key]
            self.save_memory()
            return True
        return False
    
    def has_config(self, key: str) -> bool:
        """Check if configuration key exists."""
        return key in self._memory.conf
    
    # Extended configuration management methods
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._memory.conf.copy()
    
    def set_configs(self, config_dict: Dict[str, Any]):
        """Set multiple configuration values at once."""
        for key, value in config_dict.items():
            self._memory.conf[key] = value
        self.save_memory()
    
    def update_config(self, config_dict: Dict[str, Any]):
        """Update configuration with new values (alias for set_configs)."""
        self.set_configs(config_dict)
    
    def clear_config(self):
        """Clear all configuration."""
        self._memory.conf.clear()
        self.save_memory()
    
    def get_config_keys(self) -> List[str]:
        """Get list of all configuration keys."""
        return list(self._memory.conf.keys())
    
    def get_config_count(self) -> int:
        """Get number of configuration items."""
        return len(self._memory.conf)
    
    # Nested configuration support (for keys like "model.name")
    def get_nested_config(self, key: str, default: Any = None) -> Any:
        """
        Get nested configuration value using dot notation.
        
        Args:
            key: Nested key like "model.name" or "database.host"
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._memory.conf
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_nested_config(self, key: str, value: Any):
        """
        Set nested configuration value using dot notation.
        
        Args:
            key: Nested key like "model.name" or "database.host"
            value: Value to set
        """
        keys = key.split('.')
        config = self._memory.conf
        
        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # If existing value is not a dict, replace it
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
        self.save_memory()
    
    def delete_nested_config(self, key: str) -> bool:
        """
        Delete nested configuration value using dot notation.
        
        Args:
            key: Nested key like "model.name" or "database.host"
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        keys = key.split('.')
        config = self._memory.conf
        
        try:
            # Navigate to the parent of the final key
            for k in keys[:-1]:
                config = config[k]
            
            # Delete the final key
            if keys[-1] in config:
                del config[keys[-1]]
                self.save_memory()
                return True
            else:
                return False
        except (KeyError, TypeError):
            return False
    
    def has_nested_config(self, key: str) -> bool:
        """
        Check if nested configuration key exists using dot notation.
        
        Args:
            key: Nested key like "model.name" or "database.host"
            
        Returns:
            True if key exists, False otherwise
        """
        keys = key.split('.')
        config = self._memory.conf
        
        try:
            for k in keys:
                config = config[k]
            return True
        except (KeyError, TypeError):
            return False
