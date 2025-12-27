"""
Configuration management functionality.

This module provides configuration management methods including
basic configuration, batch operations, and nested configuration support.
"""

from typing import Dict, Any, List, Literal
from pathlib import Path
from loguru import logger
from .base_manager import BaseMemoryManager
from .merge_utils import deep_merge_config, get_global_config_dir


class ConfigManagerMixin:
    """Mixin class providing configuration management functionality."""

    def _load_global_conf_dict(self) -> Dict[str, Any]:
        """
        Load global configuration dictionary from ~/.auto-coder.

        Returns:
            Global configuration dict, or empty dict if file doesn't exist
        """
        try:
            import json
            from filelock import FileLock

            global_dir = get_global_config_dir()
            global_memory_path = global_dir / "memory.json"

            if not global_memory_path.exists():
                logger.debug(f"Global config file does not exist: {global_memory_path}")
                return {}

            lock_path = str(global_memory_path) + ".lock"
            with FileLock(lock_path, timeout=30):
                with open(global_memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    global_conf = data.get("conf", {})
                    logger.debug(f"Loaded global config from {global_memory_path}")
                    return global_conf
        except Exception as e:
            logger.warning(f"Failed to load global config: {e}")
            return {}

    def get_config(
        self,
        key: str,
        default: Any = None,
        source: Literal["merged", "project", "global"] = "merged",
    ) -> Any:
        """
        Get configuration value with optional scope filtering.

        Args:
            key: Configuration key
            default: Default value if key not found
            source: Configuration source - 'merged' (default), 'project', or 'global'

        Returns:
            Configuration value from specified source
        """
        if source == "project":
            return self._memory.conf.get(key, default)
        elif source == "global":
            global_conf = self._load_global_conf_dict()
            return global_conf.get(key, default)
        else:  # merged
            global_conf = self._load_global_conf_dict()
            merged_conf = deep_merge_config(global_conf, self._memory.conf)
            return merged_conf.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set configuration value (project scope)."""
        self._memory.conf[key] = value
        self.save_memory()

    def delete_config(self, key: str) -> bool:
        """Delete configuration value (project scope)."""
        if key in self._memory.conf:
            del self._memory.conf[key]
            self.save_memory()
            return True
        return False

    def has_config(
        self, key: str, source: Literal["merged", "project", "global"] = "merged"
    ) -> bool:
        """
        Check if configuration key exists in specified source.

        Args:
            key: Configuration key
            source: Configuration source - 'merged' (default), 'project', or 'global'

        Returns:
            True if key exists in specified source
        """
        if source == "project":
            return key in self._memory.conf
        elif source == "global":
            global_conf = self._load_global_conf_dict()
            return key in global_conf
        else:  # merged
            global_conf = self._load_global_conf_dict()
            merged_conf = deep_merge_config(global_conf, self._memory.conf)
            return key in merged_conf

    # Extended configuration management methods
    def get_all_config(
        self, source: Literal["merged", "project", "global"] = "merged"
    ) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary from specified source.

        Args:
            source: Configuration source - 'merged' (default), 'project', or 'global'

        Returns:
            Configuration dictionary from specified source
        """
        if source == "project":
            return self._memory.conf.copy()
        elif source == "global":
            return self._load_global_conf_dict()
        else:  # merged
            global_conf = self._load_global_conf_dict()
            return deep_merge_config(global_conf, self._memory.conf)

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
    def get_nested_config(
        self,
        key: str,
        default: Any = None,
        source: Literal["merged", "project", "global"] = "merged",
    ) -> Any:
        """
        Get nested configuration value using dot notation.

        Args:
            key: Nested key like "model.name" or "database.host"
            default: Default value if key not found
            source: Configuration source - 'merged' (default), 'project', or 'global'

        Returns:
            Configuration value or default
        """
        keys = key.split(".")

        if source == "project":
            value = self._memory.conf
        elif source == "global":
            value = self._load_global_conf_dict()
        else:  # merged
            global_conf = self._load_global_conf_dict()
            value = deep_merge_config(global_conf, self._memory.conf)

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
        keys = key.split(".")
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
        keys = key.split(".")
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
        keys = key.split(".")
        config = self._memory.conf

        try:
            for k in keys:
                config = config[k]
            return True
        except (KeyError, TypeError):
            return False
