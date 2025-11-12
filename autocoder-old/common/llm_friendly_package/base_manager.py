"""
Base manager for LLM Friendly Package Manager

This module provides the base functionality for package management,
integrating with the core_config module for state management.
"""

import os
from typing import Optional
from rich.console import Console

from autocoder.common.core_config import get_memory_manager
from .models import RepositoryInfo


class BasePackageManager:
    """
    Base package manager providing core functionality.
    
    This class handles:
    - Integration with core_config for state management
    - Directory path management
    - Repository path management
    - Console output management
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the base package manager
        
        Args:
            project_root: Project root directory, defaults to current working directory
        """
        self.project_root = project_root or os.getcwd()
        self.memory_manager = get_memory_manager(self.project_root)
        self.console = Console()
        
        # Set up directory paths
        self.lib_dir = os.path.join(self.project_root, ".auto-coder", "libs")
        self.llm_friendly_packages_dir = os.path.join(self.lib_dir, "llm_friendly_packages")
        
        # Ensure directories exist
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Ensure required directories exist"""
        os.makedirs(self.lib_dir, exist_ok=True)
    
    @property
    def default_proxy_url(self) -> str:
        """Get default proxy URL"""
        return "https://github.com/allwefantasy/llm_friendly_packages"
    
    def _get_current_proxy(self) -> str:
        """Get current proxy URL from memory"""
        return self.memory_manager.get_config("lib-proxy", self.default_proxy_url)
    
    def _set_proxy_url(self, proxy_url: str):
        """Set proxy URL in memory"""
        self.memory_manager.set_config("lib-proxy", proxy_url)
    
    def _get_libs_config(self) -> dict:
        """Get libraries configuration from memory"""
        return self.memory_manager.get_libs()
    
    def _set_lib_config(self, lib_name: str, config: dict):
        """Set library configuration in memory"""
        self.memory_manager.add_lib(lib_name, config)
    
    def _remove_lib_config(self, lib_name: str) -> bool:
        """Remove library configuration from memory"""
        return self.memory_manager.remove_lib(lib_name)
    
    def _has_lib_config(self, lib_name: str) -> bool:
        """Check if library configuration exists in memory"""
        return self.memory_manager.has_lib(lib_name)
    
    def get_repository_info(self) -> RepositoryInfo:
        """
        Get repository information
        
        Returns:
            RepositoryInfo object with current repository state
        """
        exists = os.path.exists(self.llm_friendly_packages_dir)
        proxy_url = self._get_current_proxy()
        
        last_updated = None
        if exists:
            try:
                import git
                repo = git.Repo(self.llm_friendly_packages_dir)
                last_commit = repo.head.commit
                last_updated = last_commit.committed_datetime.isoformat()
            except Exception:
                pass
        
        return RepositoryInfo(
            exists=exists,
            url=proxy_url,
            last_updated=last_updated
        )