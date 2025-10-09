"""
Main MemoryManager class combining all functionality.

This module provides the main MemoryManager class that combines all
functionality from the various manager mixins.
"""

from typing import Optional, cast
from .base_manager import BaseMemoryManager
from .config_manager import ConfigManagerMixin
from .file_manager import FileManagerMixin
from .exclude_manager import ExcludeManagerMixin
from .lib_manager import LibManagerMixin
from .conversation_manager import ConversationManagerMixin
from .mode_manager import ModeManagerMixin
from .human_as_model_manager import HumanAsModelManagerMixin


class MemoryManager(
    BaseMemoryManager,
    ConfigManagerMixin,
    FileManagerMixin,
    ExcludeManagerMixin,
    LibManagerMixin,
    ConversationManagerMixin,
    ModeManagerMixin,
    HumanAsModelManagerMixin
):
    """
    Complete memory manager for auto-coder sessions.
    
    This class combines all functionality from various manager mixins:
    - BaseMemoryManager: Core persistence and singleton functionality
    - ConfigManagerMixin: Configuration management
    - FileManagerMixin: File and file group management
    - ExcludeManagerMixin: Exclude patterns management
    - LibManagerMixin: Library management
    - ConversationManagerMixin: Conversation history management
    - ModeManagerMixin: Mode management functionality
    - HumanAsModelManagerMixin: Human as model configuration management
    
    Provides thread-safe persistence of configuration and session data.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize memory manager with all functionality.
        
        Args:
            project_root: Project root directory. If None, uses current working directory.
        """
        super().__init__(project_root)
    
    @classmethod
    def get_instance(cls, project_root: Optional[str] = None) -> 'MemoryManager':
        """
        Get memory manager instance with proper type.
        
        Args:
            project_root: Project root directory. If None, uses current working directory.
            
        Returns:
            MemoryManager instance
        """
        return cast('MemoryManager', super().get_instance(project_root))


def get_memory_manager(project_root: Optional[str] = None) -> MemoryManager:
    """
    Get memory manager instance.
    
    Args:
        project_root: Project root directory. If None, uses current working directory.
        
    Returns:
        MemoryManager instance
    """
    return MemoryManager.get_instance(project_root)
