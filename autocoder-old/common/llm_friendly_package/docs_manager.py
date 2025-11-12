"""
Documentation manager for LLM Friendly Package Manager

This module provides functionality for managing package documentation,
including getting docs content and file paths.
"""

import os
from typing import List, Optional

from .models import DocsList


class DocsManagerMixin:
    """Mixin for documentation management functionality"""
    
    def __init__(self, project_root: Optional[str] = None):
        # This mixin assumes the base manager is already initialized
        pass
    
    def get_docs(self, package_name: Optional[str] = None, return_paths: bool = False) -> DocsList:
        """
        Get documentation for packages
        
        Args:
            package_name: Specific package name to get docs for, None for all packages
            return_paths: If True, return file paths; if False, return file contents
            
        Returns:
            List of documentation content or file paths
        """
        docs = []
        
        if not os.path.exists(self.llm_friendly_packages_dir):
            return docs
        
        libs = list(self._get_libs_config().keys())
        
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
                    
                    # Check if this is the requested package
                    if not os.path.isdir(lib_path):
                        continue
                        
                    if package_name is not None:
                        if not (lib_name == package_name or 
                               package_name == os.path.join(username, lib_name)):
                            continue
                    
                    # Check if library is added
                    if lib_name not in libs:
                        continue
                    
                    # Collect markdown files
                    for root, _, files in os.walk(lib_path):
                        for file in files:
                            if file.endswith(".md"):
                                file_path = os.path.join(root, file)
                                if return_paths:
                                    docs.append(file_path)
                                else:
                                    try:
                                        with open(file_path, "r", encoding="utf-8") as f:
                                            docs.append(f.read())
                                    except Exception as e:
                                        self.console.print(f"Error reading {file_path}: {e}")
        
        return docs
    
    def get_library_docs_paths(self, package_name: str) -> List[str]:
        """
        Get documentation file paths for a specific package
        
        Args:
            package_name: Package name
            
        Returns:
            List of markdown file paths
        """
        return self.get_docs(package_name, return_paths=True)
    
    def get_library_docs_content(self, package_name: str) -> List[str]:
        """
        Get documentation content for a specific package
        
        Args:
            package_name: Package name
            
        Returns:
            List of documentation content strings
        """
        return self.get_docs(package_name, return_paths=False)
    
    def get_all_docs_paths(self) -> List[str]:
        """Get all documentation file paths"""
        return self.get_docs(return_paths=True)
    
    def get_all_docs_content(self) -> List[str]:
        """Get all documentation content"""
        return self.get_docs(return_paths=False)
    
    def has_docs(self, package_name: str) -> bool:
        """Check if package has documentation"""
        docs = self.get_library_docs_paths(package_name)
        return len(docs) > 0
    
    def count_docs(self, package_name: Optional[str] = None) -> int:
        """Count documentation files"""
        docs = self.get_docs(package_name, return_paths=True)
        return len(docs)