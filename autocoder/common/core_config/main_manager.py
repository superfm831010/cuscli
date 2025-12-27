"""
Main MemoryManager class combining all functionality.

This module provides the main MemoryManager class that combines all
functionality from the various manager mixins.
"""

from typing import Optional, cast
from pathlib import Path
from .base_manager import BaseMemoryManager
from .config_manager import ConfigManagerMixin
from .file_manager import FileManagerMixin
from .exclude_manager import ExcludeManagerMixin
from .lib_manager import LibManagerMixin
from .conversation_manager import ConversationManagerMixin
from .mode_manager import ModeManagerMixin
from .human_as_model_manager import HumanAsModelManagerMixin
from .agentic_mode_manager import AgenticModeManagerMixin
from .merge_utils import get_global_config_dir


class MemoryManager(
    BaseMemoryManager,
    ConfigManagerMixin,
    FileManagerMixin,
    ExcludeManagerMixin,
    LibManagerMixin,
    ConversationManagerMixin,
    ModeManagerMixin,
    HumanAsModelManagerMixin,
    AgenticModeManagerMixin,
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
    - AgenticModeManagerMixin: Agentic mode configuration management

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
    def get_instance(cls, project_root: Optional[str] = None) -> "MemoryManager":
        """
        Get memory manager instance with proper type.

        Args:
            project_root: Project root directory. If None, uses current working directory.

        Returns:
            MemoryManager instance
        """
        return cast("MemoryManager", super().get_instance(project_root))


def get_memory_manager(project_root: Optional[str] = None) -> MemoryManager:
    """
    Get memory manager instance.

    Args:
        project_root: Project root directory. If None, uses current working directory.

    Returns:
        MemoryManager instance
    """
    return MemoryManager.get_instance(project_root)


def get_global_memory_manager() -> MemoryManager:
    """
    Get global memory manager instance.

    This returns a MemoryManager instance that persists to ~/.auto-coder
    instead of the current project directory.

    Returns:
        MemoryManager instance for global configuration
    """
    global_dir = get_global_config_dir()
    # Use the parent of plugins/chat-auto-coder as the "project root"
    # so the manager creates .auto-coder/plugins/chat-auto-coder under home
    global_root = str(global_dir.parent.parent.parent)  # Points to home directory
    return MemoryManager.get_instance(global_root)
