"""
Data models for LLM Friendly Package Manager

This module defines the core data structures used throughout the package manager.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LibraryInfo:
    """Information about a library in the repository"""
    domain: str
    username: str
    lib_name: str
    full_path: str
    is_added: bool
    has_md_files: bool = True


@dataclass
class PackageDoc:
    """Package documentation information"""
    file_path: str
    content: Optional[str] = None


@dataclass
class RepositoryInfo:
    """Information about the repository state"""
    exists: bool
    url: str
    last_updated: Optional[str] = None


# Type aliases for better type hints
LibraryList = List[LibraryInfo]
DocsList = List[str]
ConfigDict = Dict[str, Any]