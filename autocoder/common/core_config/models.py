"""
Core data models for memory management.

This module contains the data structures used by the memory management system.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class CoreMemory:
    """Core memory data structure for auto-coder sessions."""
    
    conversation: List[Dict[str, str]] = field(default_factory=list)
    current_files: Dict[str, Any] = field(default_factory=lambda: {
        "files": [], 
        "groups": {}, 
        "groups_info": {}, 
        "current_groups": []
    })
    conf: Dict[str, Any] = field(default_factory=dict)
    exclude_dirs: List[str] = field(default_factory=list)
    exclude_files: List[str] = field(default_factory=list)
    libs: Dict[str, Any] = field(default_factory=dict)
    mode: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "conversation": self.conversation,
            "current_files": self.current_files,
            "conf": self.conf,
            "exclude_dirs": self.exclude_dirs,
            "exclude_files": self.exclude_files,
            "libs": self.libs,
            "mode": self.mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreMemory':
        """Create CoreMemory instance from dictionary data."""
        # Ensure current_files has all required keys
        current_files = data.get("current_files", {})
        if not isinstance(current_files, dict):
            current_files = {"files": [], "groups": {}, "groups_info": {}, "current_groups": []}
        else:
            current_files.setdefault("files", [])
            current_files.setdefault("groups", {})
            current_files.setdefault("groups_info", {})
            current_files.setdefault("current_groups", [])
        
        return cls(
            conversation=data.get("conversation", []),
            current_files=current_files,
            conf=data.get("conf", {}),
            exclude_dirs=data.get("exclude_dirs", []),
            exclude_files=data.get("exclude_files", []),
            libs=data.get("libs", {}),
            mode=data.get("mode", "normal"),
        )


# Type aliases for better code clarity
ConfigDict = Dict[str, Any]
FileList = List[str]
GroupsDict = Dict[str, List[str]]
GroupsInfoDict = Dict[str, Dict[str, Any]]
LibsDict = Dict[str, Any]
ConversationList = List[Dict[str, str]]
