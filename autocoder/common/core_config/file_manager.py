"""
File and file group management functionality.

This module provides methods for managing current files, file groups,
group information, and active groups.
"""

from typing import Dict, Any, List
from .models import FileList, GroupsDict, GroupsInfoDict


class FileManagerMixin:
    """Mixin class providing file and file group management functionality."""
    
    # ===== File Management =====
    def get_current_files(self) -> FileList:
        """Get current files list."""
        return self._memory.current_files.get("files", [])
    
    def set_current_files(self, files: FileList):
        """Set current files list."""
        self._memory.current_files["files"] = files
        self.save_memory()
    
    def add_files(self, files: FileList) -> FileList:
        """Add files to current files list (avoiding duplicates)."""
        current_files = set(self._memory.current_files.get("files", []))
        new_files = [f for f in files if f not in current_files]
        if new_files:
            self._memory.current_files["files"].extend(new_files)
            self.save_memory()
        return new_files
    
    def remove_files(self, files: FileList) -> FileList:
        """Remove files from current files list."""
        current_files = self._memory.current_files.get("files", [])
        removed_files = []
        for file in files:
            if file in current_files:
                current_files.remove(file)
                removed_files.append(file)
        if removed_files:
            self.save_memory()
        return removed_files
    
    def clear_files(self):
        """Clear all current files."""
        self._memory.current_files["files"] = []
        self.save_memory()
    
    # ===== File Groups Management =====
    def get_file_groups(self) -> GroupsDict:
        """Get all file groups."""
        return self._memory.current_files.get("groups", {})
    
    def get_file_group(self, name: str) -> FileList:
        """Get files in a specific group."""
        return self._memory.current_files.get("groups", {}).get(name, [])
    
    def set_file_group(self, name: str, files: FileList):
        """Set files for a group."""
        if "groups" not in self._memory.current_files:
            self._memory.current_files["groups"] = {}
        self._memory.current_files["groups"][name] = files
        self.save_memory()
    
    def add_file_group(self, name: str, files: FileList):
        """Add a new file group with current files or specified files."""
        if not files:
            files = self.get_current_files().copy()
        self.set_file_group(name, files)
    
    def delete_file_group(self, name: str) -> bool:
        """Delete a file group."""
        groups = self._memory.current_files.get("groups", {})
        if name in groups:
            del groups[name]
            # Also remove from groups_info and current_groups
            groups_info = self._memory.current_files.get("groups_info", {})
            if name in groups_info:
                del groups_info[name]
            current_groups = self._memory.current_files.get("current_groups", [])
            if name in current_groups:
                current_groups.remove(name)
            self.save_memory()
            return True
        return False
    
    def has_file_group(self, name: str) -> bool:
        """Check if file group exists."""
        return name in self._memory.current_files.get("groups", {})
    
    # ===== File Groups Info Management =====
    def get_groups_info(self) -> GroupsInfoDict:
        """Get all groups info."""
        return self._memory.current_files.get("groups_info", {})
    
    def get_group_info(self, name: str) -> Dict[str, Any]:
        """Get info for a specific group."""
        return self._memory.current_files.get("groups_info", {}).get(name, {})
    
    def set_group_info(self, name: str, info: Dict[str, Any]):
        """Set info for a group."""
        if "groups_info" not in self._memory.current_files:
            self._memory.current_files["groups_info"] = {}
        self._memory.current_files["groups_info"][name] = info
        self.save_memory()
    
    def set_group_query_prefix(self, name: str, query_prefix: str):
        """Set query prefix for a group."""
        info = self.get_group_info(name)
        info["query_prefix"] = query_prefix
        self.set_group_info(name, info)
    
    def get_group_query_prefix(self, name: str) -> str:
        """Get query prefix for a group."""
        return self.get_group_info(name).get("query_prefix", "")
    
    # ===== Current Active Groups Management =====
    def get_current_groups(self) -> List[str]:
        """Get currently active groups."""
        return self._memory.current_files.get("current_groups", [])
    
    def set_current_groups(self, groups: List[str]):
        """Set currently active groups."""
        self._memory.current_files["current_groups"] = groups
        self.save_memory()
    
    def add_current_group(self, group_name: str):
        """Add group to current active groups."""
        current_groups = self._memory.current_files.get("current_groups", [])
        if group_name not in current_groups:
            current_groups.append(group_name)
            self.save_memory()
    
    def remove_current_group(self, group_name: str) -> bool:
        """Remove group from current active groups."""
        current_groups = self._memory.current_files.get("current_groups", [])
        if group_name in current_groups:
            current_groups.remove(group_name)
            self.save_memory()
            return True
        return False
    
    def clear_current_groups(self):
        """Clear all current active groups."""
        self._memory.current_files["current_groups"] = []
        self.save_memory()
    
    def merge_groups_to_current_files(self, group_names: List[str]) -> List[str]:
        """Merge files from multiple groups and set as current files."""
        merged_files = set()
        existing_groups = []
        missing_groups = []
        
        groups = self.get_file_groups()
        for group_name in group_names:
            if group_name in groups:
                merged_files.update(groups[group_name])
                existing_groups.append(group_name)
            else:
                missing_groups.append(group_name)
        
        if merged_files:
            self.set_current_files(list(merged_files))
            self.set_current_groups(existing_groups)
        
        return missing_groups
    
    # ===== Legacy File Group Helpers =====
    def get_groups(self) -> GroupsDict:
        """Get file groups (legacy method for backward compatibility)."""
        return self.get_file_groups()
    
    def set_group(self, name: str, files: FileList):
        """Set a file group (legacy method for backward compatibility)."""
        self.set_file_group(name, files)
