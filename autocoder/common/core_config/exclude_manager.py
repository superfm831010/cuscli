"""
Exclude management functionality.

This module provides methods for managing excluded files and directories.
"""

from typing import List
from .models import FileList


class ExcludeManagerMixin:
    """Mixin class providing exclude management functionality."""
    
    # ===== Exclude Files Management =====
    def get_exclude_files(self) -> FileList:
        """Get exclude file patterns."""
        return self._memory.exclude_files.copy()
    
    def add_exclude_files(self, patterns: FileList) -> FileList:
        """Add exclude file patterns (avoiding duplicates)."""
        existing_patterns = set(self._memory.exclude_files)
        new_patterns = [p for p in patterns if p not in existing_patterns]
        if new_patterns:
            self._memory.exclude_files.extend(new_patterns)
            self.save_memory()
        return new_patterns
    
    def remove_exclude_files(self, patterns: FileList) -> FileList:
        """Remove exclude file patterns."""
        removed_patterns = []
        for pattern in patterns:
            if pattern in self._memory.exclude_files:
                self._memory.exclude_files.remove(pattern)
                removed_patterns.append(pattern)
        if removed_patterns:
            self.save_memory()
        return removed_patterns
    
    def clear_exclude_files(self):
        """Clear all exclude file patterns."""
        self._memory.exclude_files = []
        self.save_memory()
    
    # ===== Exclude Directories Management =====
    def get_exclude_dirs(self) -> List[str]:
        """Get exclude directories."""
        return self._memory.exclude_dirs.copy()
    
    def add_exclude_dirs(self, dirs: List[str]) -> List[str]:
        """Add exclude directories (avoiding duplicates)."""
        existing_dirs = set(self._memory.exclude_dirs)
        new_dirs = [d for d in dirs if d not in existing_dirs]
        if new_dirs:
            self._memory.exclude_dirs.extend(new_dirs)
            self.save_memory()
        return new_dirs
    
    def remove_exclude_dirs(self, dirs: List[str]) -> List[str]:
        """Remove exclude directories."""
        removed_dirs = []
        for dir_name in dirs:
            if dir_name in self._memory.exclude_dirs:
                self._memory.exclude_dirs.remove(dir_name)
                removed_dirs.append(dir_name)
        if removed_dirs:
            self.save_memory()
        return removed_dirs
    
    def clear_exclude_dirs(self):
        """Clear all exclude directories."""
        self._memory.exclude_dirs = []
        self.save_memory()
