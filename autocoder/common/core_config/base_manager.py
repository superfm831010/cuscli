"""
Base memory manager providing core persistence functionality.

This module contains the base MemoryManager class with core functionality
for loading, saving, and managing memory persistence.
"""

import os
import json
import threading
from typing import Dict, Any, Optional
from filelock import FileLock
from loguru import logger

from .models import CoreMemory


class BaseMemoryManager:
    """
    Base memory manager providing core persistence functionality.
    
    This class handles:
    - Memory persistence (load/save)
    - File locking for thread safety
    - Singleton pattern management
    - Directory creation
    """
    
    _instances: Dict[str, 'BaseMemoryManager'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, project_root: Optional[str] = None):
        """Ensure singleton pattern for each project root."""
        root = os.path.abspath(project_root or os.getcwd())
        with cls._lock:
            if root not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[root] = instance
            return cls._instances[root]
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize base memory manager.
        
        Args:
            project_root: Project root directory. If None, uses current working directory.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
            
        self.project_root = os.path.abspath(project_root or os.getcwd())
        self.base_persist_dir = os.path.join(
            self.project_root, ".auto-coder", "plugins", "chat-auto-coder"
        )
        self._memory = CoreMemory()
        self._ensure_dirs()
        self.load_memory()
        self._initialized = True
    
    @classmethod
    def get_instance(cls, project_root: Optional[str] = None) -> 'BaseMemoryManager':
        """
        Get singleton instance for a project root.
        
        Args:
            project_root: Project root directory. If None, uses current working directory.
            
        Returns:
            BaseMemoryManager instance
        """
        root = os.path.abspath(project_root or os.getcwd())
        return cls(root)
    
    def _ensure_dirs(self):
        """Ensure persistence directories exist."""
        os.makedirs(self.base_persist_dir, exist_ok=True)
    
    @property
    def memory_path(self) -> str:
        """Get memory file path."""
        return os.path.join(self.base_persist_dir, "memory.json")
    
    @property
    def lock_path(self) -> str:
        """Get lock file path."""
        return self.memory_path + ".lock"
    
    def save_memory(self):
        """Save current memory to disk."""
        with FileLock(self.lock_path, timeout=30):
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self._memory.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Memory saved to {self.memory_path}")
    
    def save_memory_with_new_memory(self, new_memory: Dict[str, Any]):
        """Save new memory data to disk."""
        with FileLock(self.lock_path, timeout=30):
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(new_memory, f, indent=2, ensure_ascii=False)
            # Update internal memory state while we have the lock
            self._memory = CoreMemory.from_dict(new_memory)
        
        logger.debug(f"New memory saved to {self.memory_path}")
    
    def load_memory(self) -> CoreMemory:
        """Load memory from disk."""
        if os.path.exists(self.memory_path):
            with FileLock(self.lock_path, timeout=30):
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._memory = CoreMemory.from_dict(data)
                logger.debug(f"Memory loaded from {self.memory_path}")
        return self._memory
    
    def get_memory(self) -> CoreMemory:
        """Get current memory (reloads from disk)."""
        return self.load_memory()
    
    def get_memory_dict(self) -> Dict[str, Any]:
        """Get memory as dictionary."""
        return self.get_memory().to_dict()
