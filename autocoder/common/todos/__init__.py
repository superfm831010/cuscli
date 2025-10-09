"""
Todos management module for AutoCoder.

This module provides comprehensive todo and task management functionality
with conversation-based storage, caching, and session management.
"""

from .exceptions import (
    TodoManagerError,
    TodoNotFoundError,
    TodoListNotFoundError
)

from .models import (
    Todo,
    TodoList
)

from .config import TodoManagerConfig

# Storage layer
from .storage import (
    BaseStorage,
    FileStorage
)

# Cache layer
from .cache import (
    BaseCache,
    MemoryCache,
    CacheManager
)

# Main manager
from .manager import TodoManager

__all__ = [
    # Main manager
    'TodoManager',
    
    # Exceptions
    'TodoManagerError',
    'TodoNotFoundError',
    'TodoListNotFoundError',
    
    # Models
    'Todo',
    'TodoList',
    
    # Configuration
    'TodoManagerConfig',
    
    # Storage layer
    'BaseStorage',
    'FileStorage',
    
    # Cache layer
    'BaseCache',
    'MemoryCache',
    'CacheManager'
] 