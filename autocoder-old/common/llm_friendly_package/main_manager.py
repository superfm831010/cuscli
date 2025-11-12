"""
Main LLM Friendly Package Manager

This module provides the complete package management functionality,
integrating with the core_config module for state management.
"""

import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
import git
from git import GitCommandError

from autocoder.common.core_config import get_memory_manager
from .models import LibraryInfo, LibraryList, DocsList, RepositoryInfo


class LLMFriendlyPackageManager:
    """
    Complete LLM Friendly Package Manager
    
    This class provides all package management functionality including:
    - Library management (add, remove, list)
    - Documentation management (get docs, paths)
    - Repository management (clone, refresh, proxy)
    - Display management (tables, output)
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the package manager
        
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
    
    # ======== Library Management ========
    
    def list_added_libraries(self) -> List[str]:
        """List all added libraries"""
        return list(self.memory_manager.get_libs().keys())
    
    def list_all_available_libraries(self) -> LibraryList:
        """List all available libraries in the repository"""
        if not os.path.exists(self.llm_friendly_packages_dir):
            return []
        
        available_libs = []
        added_libs = set(self.memory_manager.get_libs().keys())
        
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
        
        if self.memory_manager.has_lib(lib_name):
            self.console.print(f"Library {lib_name} is already added")
            return False
        
        self.memory_manager.add_lib(lib_name, {})
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
        if not self.memory_manager.has_lib(lib_name):
            self.console.print(f"Library {lib_name} is not in the list")
            return False
        
        self.memory_manager.remove_lib(lib_name)
        self.console.print(f"Removed library: {lib_name}")
        return True
    
    def has_library(self, lib_name: str) -> bool:
        """Check if library is added"""
        return self.memory_manager.has_lib(lib_name)
    
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
    
    # ======== Documentation Management ========
    
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
        
        libs = list(self.memory_manager.get_libs().keys())
        
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
        """Get documentation file paths for a specific package"""
        return self.get_docs(package_name, return_paths=True)
    
    def get_library_docs_content(self, package_name: str) -> List[str]:
        """Get documentation content for a specific package"""
        return self.get_docs(package_name, return_paths=False)
    
    # ======== Repository Management ========
    
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
        except GitCommandError as e:
            self.console.print(f"Error cloning repository: {e}")
            return False
    
    def refresh_repository(self) -> bool:
        """Refresh the repository by pulling latest changes"""
        if not os.path.exists(self.llm_friendly_packages_dir):
            self.console.print(
                "llm_friendly_packages repository does not exist. "
                "Please call add_library() first to clone it."
            )
            return False
        
        try:
            repo = git.Repo(self.llm_friendly_packages_dir)
            origin = repo.remotes.origin
            
            # Update remote URL if proxy is set
            proxy_url = self._get_current_proxy()
            current_url = origin.url
            
            if proxy_url and proxy_url != current_url:
                origin.set_url(proxy_url)
                self.console.print(f"Updated remote URL to: {proxy_url}")
            
            origin.pull()
            self.console.print("Successfully updated llm_friendly_packages repository")
            return True
            
        except GitCommandError as e:
            self.console.print(f"Error updating repository: {e}")
            return False
    
    def set_proxy(self, proxy_url: Optional[str] = None) -> str:
        """Set or get proxy URL"""
        if proxy_url is None:
            current_proxy = self._get_current_proxy()
            self.console.print(f"Current proxy: {current_proxy}")
            return current_proxy
        
        self.memory_manager.set_config("lib-proxy", proxy_url)
        self.console.print(f"Set proxy to: {proxy_url}")
        return proxy_url
    
    def get_repository_info(self) -> RepositoryInfo:
        """Get repository information"""
        exists = os.path.exists(self.llm_friendly_packages_dir)
        proxy_url = self._get_current_proxy()
        
        last_updated = None
        if exists:
            try:
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
    
    # ======== Display Management ========
    
    def display_added_libraries(self) -> None:
        """Display added libraries in a table"""
        libs = self.list_added_libraries()
        
        if not libs:
            self.console.print("No libraries added yet")
            return
        
        table = Table(title="Added Libraries")
        table.add_column("Library Name", style="cyan")
        
        for lib_name in libs:
            table.add_row(lib_name)
        
        self.console.print(table)
    
    def display_all_libraries(self) -> None:
        """Display all available libraries in a table"""
        if not os.path.exists(self.llm_friendly_packages_dir):
            self.console.print(
                "llm_friendly_packages repository does not exist. "
                "Please call add_library() first to clone it."
            )
            return
        
        available_libs = self.list_all_available_libraries()
        
        if not available_libs:
            self.console.print("No available libraries found in the repository.")
            return
        
        table = Table(title="Available Libraries")
        table.add_column("Domain", style="blue")
        table.add_column("Username", style="green")
        table.add_column("Library Name", style="cyan")
        table.add_column("Full Path", style="magenta")
        table.add_column("Status", style="yellow")
        
        for lib in available_libs:
            status = "[green]Added[/green]" if lib.is_added else "[white]Not Added[/white]"
            table.add_row(
                lib.domain,
                lib.username,
                lib.lib_name,
                lib.full_path,
                status
            )
        
        self.console.print(table)
    
    def display_library_docs(self, package_name: str) -> None:
        """Display documentation paths for a package in a table"""
        docs = self.get_library_docs_paths(package_name)
        
        if not docs:
            self.console.print(f"No markdown files found for package: {package_name}")
            return
        
        table = Table(title=f"Markdown Files for {package_name}")
        table.add_column("File Path", style="cyan")
        
        for doc in docs:
            table.add_row(doc)
        
        self.console.print(table)


def get_package_manager(project_root: Optional[str] = None) -> LLMFriendlyPackageManager:
    """
    Get package manager instance
    
    Args:
        project_root: Project root directory
        
    Returns:
        LLMFriendlyPackageManager instance
    """
    return LLMFriendlyPackageManager(project_root)