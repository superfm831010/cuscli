"""
Global todo manager singleton accessor.

This module provides a global singleton accessor for the todo manager,
ensuring only one instance exists across the application.
"""

import os
import threading
from typing import Optional
from .manager import TodoManager
from .config import TodoManagerConfig


class TodoManagerSingleton:
    """Todo manager singleton class, ensuring only one global instance"""
    
    _instance: Optional[TodoManager] = None
    _lock = threading.Lock()
    _config: Optional[TodoManagerConfig] = None
    
    @classmethod
    def get_instance(cls, config: Optional[TodoManagerConfig] = None) -> TodoManager:
        """
        Get todo manager instance
        
        Args:
            config: Configuration object, if None uses default config
            
        Returns:
            TodoManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        config = cls._get_default_config()
                    cls._config = config
                    cls._instance = TodoManager(config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls, config: Optional[TodoManagerConfig] = None):
        """
        Reset instance, used for testing or configuration changes
        
        Args:
            config: New configuration object
        """
        with cls._lock:
            cls._instance = None
            cls._config = None
            if config is not None:
                cls._instance = TodoManager(config)
                cls._config = config
    
    @classmethod
    def _get_default_config(cls) -> TodoManagerConfig:
        """Get default configuration"""
        # Default storage path in .auto-coder/todos
        default_storage_path = os.path.join(os.getcwd(), ".auto-coder", "todos")
        
        return TodoManagerConfig(
            storage_path=default_storage_path,
            max_cache_size=50,
            cache_ttl=300.0,
            enable_compression=False,
            log_level="INFO"
        )
    
    @classmethod
    def get_config(cls) -> Optional[TodoManagerConfig]:
        """Get current configuration"""
        return cls._config


def get_todo_manager(config: Optional[TodoManagerConfig] = None) -> TodoManager:
    """
    Get global todo manager instance
    
    This is a convenience function that uses singleton pattern to ensure
    only one instance exists globally. First call creates the instance,
    subsequent calls return the same instance.
    
    Args:
        config: Optional configuration object. If None, default config is used.
               Note: config parameter only takes effect on first call.
    
    Returns:
        TodoManager: Todo manager instance
        
    Example:
        ```python
        # Use default configuration
        manager = get_todo_manager()
        
        # Use custom configuration (only takes effect on first call)
        config = TodoManagerConfig(
            storage_path="./my_todos",
            max_cache_size=100
        )
        manager = get_todo_manager(config)
        
        # Create todos
        todo_ids = manager.create_todos(
            content="Implement todo feature\nWrite tests\nUpdate docs"
        )
        ```
    """
    return TodoManagerSingleton.get_instance(config)


def get_manager(config: Optional[TodoManagerConfig] = None) -> TodoManager:
    """
    Alias for get_todo_manager for convenience
    
    Returns:
        TodoManager instance
    """
    return get_todo_manager(config)


def reset_todo_manager(config: Optional[TodoManagerConfig] = None):
    """
    Reset todo manager instance
    
    This function is mainly used for testing or when configuration needs to change.
    After calling this function, the next call to get_todo_manager() will create
    a new instance with the new configuration.
    
    Args:
        config: New configuration object
        
    Example:
        ```python
        # Reset with new configuration
        new_config = TodoManagerConfig(storage_path="./test_todos")
        reset_todo_manager(new_config)
        
        # Next call will use new configuration
        manager = get_todo_manager()
        ```
    """
    TodoManagerSingleton.reset_instance(config)


def reset_manager(config: Optional[TodoManagerConfig] = None):
    """
    Alias for reset_todo_manager for convenience
    """
    reset_todo_manager(config)


def get_todo_manager_config() -> Optional[TodoManagerConfig]:
    """
    Get current todo manager configuration
    
    Returns:
        Current configuration object, or None if not yet initialized
    """
    return TodoManagerSingleton.get_config() 