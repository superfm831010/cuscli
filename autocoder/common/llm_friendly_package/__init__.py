"""
LLM Friendly Package Manager Module

This module provides a complete interface for managing LLM friendly packages,
integrating with the core_config module for state management.
"""

from .main_manager import LLMFriendlyPackageManager, get_package_manager
from .models import LibraryInfo, PackageDoc, RepositoryInfo, LibraryList, DocsList, ConfigDict

# Main exports
__all__ = [
    # Main classes
    "LLMFriendlyPackageManager",
    
    # Convenience functions
    "get_package_manager",
    
    # Data models
    "LibraryInfo",
    "PackageDoc", 
    "RepositoryInfo",
    
    # Type aliases
    "LibraryList",
    "DocsList",
    "ConfigDict",
]

# Backward compatibility - expose the main class with simpler name
PackageManager = LLMFriendlyPackageManager