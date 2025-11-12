"""
Library manager for LLM Friendly Package Manager

This module provides functionality for managing library operations
such as add, remove, list, and configuration management.
"""

import os
from typing import List, Optional, Set
import git

from .base_manager import BasePackageManager
from .models import LibraryInfo, LibraryList


class LibraryManagerMixin:
    """Mixin for library management functionality"""
    
    def __init__(self, project_root: Optional[str] = None):
        # This mixin assumes the base manager is already initialized
        pass
    
    def list_added_libraries(self) -> List[str]:
        """List all added libraries"""
        return list(self._get_libs_config().keys())
    
    def list_all_available_libraries(self) -> LibraryList:
        """List all available libraries in the repository"""
        if not os.path.exists(self.llm_friendly_packages_dir):
            return []
        
        available_libs = []
        added_libs = set(self._get_libs_config().keys())
        
        for domain in os.listdir(self.llm_friendly_packages_dir):
            domain_path = os.path.join(self.llm_friendly_packages_dir, domain)
            if not os.path.isdir(domain_path):
                continue
                
            for username in os.listdir(domain_path):
                username_path = os.path.join(domain_path, username)
                if not os.path.isdir(username_path):
                    continue
                    
                for lib_name in os.listdir(username_path):
                    lib_path = os.path.join(username_path, lib_name)
                    if not os.path.isdir(lib_path):
                        continue
                    
                    # Check if has markdown files
                    has_md_files = False
                    for root, _, files in os.walk(lib_path):
                        if any(file.endswith('.md') for file in files):
                            has_md_files = True
                            break
                    
                    if has_md_files:
                        available_libs.append(LibraryInfo(
                            domain=domain,
                            username=username,
                            lib_name=lib_name,
                            full_path=f"{username}/{lib_name}",
                            is_added=lib_name in added_libs,
                            has_md_files=has_md_files
                        ))
        
        # Sort by domain, username, lib_name
        available_libs.sort(key=lambda x: (x.domain, x.username, x.lib_name))
        return available_libs
    
    def add_library(self, lib_name: str) -> bool:
        """
        Add a library to the list
        
        Args:
            lib_name: Library name to add
            
        Returns:
            True if successful, False otherwise
        """
        # Clone repository if needed
        if not self._clone_repository():
            return False
        
        if self._has_lib_config(lib_name):
            self.console.print(f"Library {lib_name} is already added")
            return False
        
        self._set_lib_config(lib_name, {})
        self.console.print(f"Added library: {lib_name}")
        return True
    
    def remove_library(self, lib_name: str) -> bool:
        """
        Remove a library from the list
        
        Args:
            lib_name: Library name to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self._has_lib_config(lib_name):
            self.console.print(f"Library {lib_name} is not in the list")
            return False
        
        self._remove_lib_config(lib_name)
        self.console.print(f"Removed library: {lib_name}")
        return True
    
    def has_library(self, lib_name: str) -> bool:
        """Check if library is added"""
        return self._has_lib_config(lib_name)
    
    def get_library_config(self, lib_name: str) -> dict:
        """Get library configuration"""
        return self.memory_manager.get_lib_config(lib_name)
    
    def set_library_config(self, lib_name: str, config: dict):
        """Set library configuration"""
        self.memory_manager.set_lib_config(lib_name, config)
    
    def get_package_path(self, package_name: str) -> Optional[str]:
        """
        Get the full path of a package by its name
        
        Args:
            package_name: Package name (can be just lib_name or username/lib_name)
            
        Returns:
            Full path to the package directory, or None if not found
        """
        if not os.path.exists(self.llm_friendly_packages_dir):
            return None
        
        for domain in os.listdir(self.llm_friendly_packages_dir):
            domain_path = os.path.join(self.llm_friendly_packages_dir, domain)
            if not os.path.isdir(domain_path):
                continue
                
            for username in os.listdir(domain_path):
                username_path = os.path.join(domain_path, username)
                if not os.path.isdir(username_path):
                    continue
                    
                for lib_name in os.listdir(username_path):
                    lib_path = os.path.join(username_path, lib_name)
                    if not os.path.isdir(lib_path):
                        continue
                    
                    # Check if this matches the requested package
                    if (lib_name == package_name or 
                        package_name == os.path.join(username, lib_name)):
                        return lib_path
        
        return None
    
    def _clone_repository(self) -> bool:
        """Clone the llm_friendly_packages repository"""
        if os.path.exists(self.llm_friendly_packages_dir):
            return True
            
        self.console.print("Cloning llm_friendly_packages repository...")
        try:
            proxy_url = self._get_current_proxy()
            git.Repo.clone_from(proxy_url, self.llm_friendly_packages_dir)
            self.console.print("Successfully cloned llm_friendly_packages repository")
            return True
        except git.exc.GitCommandError as e:
            self.console.print(f"Error cloning repository: {e}")
            return False