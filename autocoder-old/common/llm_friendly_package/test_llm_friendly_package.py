"""
Test suite for LLM Friendly Package Manager

This module provides comprehensive tests for all package manager functionality
including library management, documentation handling, repository operations,
and integration with core_config.
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from autocoder.common.llm_friendly_package import (
    LLMFriendlyPackageManager,
    get_package_manager,
    LibraryInfo,
    RepositoryInfo,
    PackageDoc
)


class TestLLMFriendlyPackageManager:
    """Test suite for LLMFriendlyPackageManager"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock memory manager for testing"""
        mock_manager = Mock()
        mock_manager.get_libs.return_value = {}
        mock_manager.get_config.return_value = "https://github.com/allwefantasy/llm_friendly_packages"
        mock_manager.has_lib.return_value = False
        mock_manager.add_lib.return_value = None
        mock_manager.remove_lib.return_value = True
        mock_manager.set_config.return_value = None
        return mock_manager
    
    @pytest.fixture
    def manager(self, temp_project_root, mock_memory_manager):
        """Create a package manager instance for testing"""
        with patch('autocoder.common.llm_friendly_package.main_manager.get_memory_manager') as mock_get_memory:
            mock_get_memory.return_value = mock_memory_manager
            return LLMFriendlyPackageManager(temp_project_root)
    
    @pytest.fixture
    def mock_repo_structure(self, manager):
        """Create a mock repository structure for testing"""
        repo_dir = manager.llm_friendly_packages_dir
        os.makedirs(repo_dir, exist_ok=True)
        
        # Create test library structure
        test_lib_path = os.path.join(repo_dir, "github.com", "testuser", "testlib")
        os.makedirs(test_lib_path, exist_ok=True)
        
        # Create test markdown file
        readme_path = os.path.join(test_lib_path, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Test Library\n\nThis is a test library for LLM.")
        
        # Create another test library
        test_lib2_path = os.path.join(repo_dir, "github.com", "testuser", "testlib2")
        os.makedirs(test_lib2_path, exist_ok=True)
        
        docs_path = os.path.join(test_lib2_path, "docs.md")
        with open(docs_path, "w") as f:
            f.write("# Test Library 2 Documentation\n\nDetailed docs here.")
        
        return repo_dir
    
    def test_manager_initialization(self, temp_project_root, mock_memory_manager):
        """Test manager initialization"""
        with patch('autocoder.common.llm_friendly_package.main_manager.get_memory_manager') as mock_get_memory:
            mock_get_memory.return_value = mock_memory_manager
            
            manager = LLMFriendlyPackageManager(temp_project_root)
            
            assert manager.project_root == temp_project_root
            assert manager.memory_manager == mock_memory_manager
            assert manager.lib_dir == os.path.join(temp_project_root, ".auto-coder", "libs")
            assert os.path.exists(manager.lib_dir)
    
    def test_get_package_manager_function(self, temp_project_root, mock_memory_manager):
        """Test the convenience function"""
        with patch('autocoder.common.llm_friendly_package.main_manager.get_memory_manager') as mock_get_memory:
            mock_get_memory.return_value = mock_memory_manager
            
            manager = get_package_manager(temp_project_root)
            assert isinstance(manager, LLMFriendlyPackageManager)
            assert manager.project_root == temp_project_root
    
    def test_default_proxy_url(self, manager):
        """Test default proxy URL"""
        assert manager.default_proxy_url == "https://github.com/allwefantasy/llm_friendly_packages"
    
    def test_list_added_libraries_empty(self, manager):
        """Test listing libraries when none are added"""
        libs = manager.list_added_libraries()
        assert libs == []
    
    def test_list_added_libraries_with_data(self, manager, mock_memory_manager):
        """Test listing libraries with data"""
        mock_memory_manager.get_libs.return_value = {"numpy": {}, "pandas": {}}
        
        libs = manager.list_added_libraries()
        assert set(libs) == {"numpy", "pandas"}
    
    def test_add_library_success(self, manager, mock_memory_manager):
        """Test successful library addition"""
        mock_memory_manager.has_lib.return_value = False
        
        with patch.object(manager, '_clone_repository', return_value=True):
            result = manager.add_library("test-lib")
            
            assert result is True
            mock_memory_manager.add_lib.assert_called_once_with("test-lib", {})
    
    def test_add_library_already_exists(self, manager, mock_memory_manager):
        """Test adding library that already exists"""
        mock_memory_manager.has_lib.return_value = True
        
        with patch.object(manager, '_clone_repository', return_value=True):
            result = manager.add_library("existing-lib")
            
            assert result is False
            mock_memory_manager.add_lib.assert_not_called()
    
    def test_add_library_clone_fails(self, manager, mock_memory_manager):
        """Test library addition when repository clone fails"""
        mock_memory_manager.has_lib.return_value = False
        
        with patch.object(manager, '_clone_repository', return_value=False):
            result = manager.add_library("test-lib")
            
            assert result is False
            mock_memory_manager.add_lib.assert_not_called()
    
    def test_remove_library_success(self, manager, mock_memory_manager):
        """Test successful library removal"""
        mock_memory_manager.has_lib.return_value = True
        
        result = manager.remove_library("test-lib")
        
        assert result is True
        mock_memory_manager.remove_lib.assert_called_once_with("test-lib")
    
    def test_remove_library_not_found(self, manager, mock_memory_manager):
        """Test removing library that doesn't exist"""
        mock_memory_manager.has_lib.return_value = False
        
        result = manager.remove_library("nonexistent-lib")
        
        assert result is False
        mock_memory_manager.remove_lib.assert_not_called()
    
    def test_has_library(self, manager, mock_memory_manager):
        """Test checking if library exists"""
        mock_memory_manager.has_lib.side_effect = lambda name: name == "existing-lib"
        
        assert manager.has_library("existing-lib") is True
        assert manager.has_library("nonexistent-lib") is False
    
    def test_list_all_available_libraries_no_repo(self, manager):
        """Test listing available libraries when repository doesn't exist"""
        libs = manager.list_all_available_libraries()
        assert libs == []
    
    def test_list_all_available_libraries_with_repo(self, manager, mock_repo_structure, mock_memory_manager):
        """Test listing available libraries with repository"""
        mock_memory_manager.get_libs.return_value = {"testlib": {}}
        
        libs = manager.list_all_available_libraries()
        
        assert len(libs) == 2
        
        # Check first library
        lib1 = next(lib for lib in libs if lib.lib_name == "testlib")
        assert lib1.domain == "github.com"
        assert lib1.username == "testuser"
        assert lib1.lib_name == "testlib"
        assert lib1.full_path == "testuser/testlib"
        assert lib1.is_added is True
        assert lib1.has_md_files is True
        
        # Check second library
        lib2 = next(lib for lib in libs if lib.lib_name == "testlib2")
        assert lib2.is_added is False
    
    def test_get_package_path_found(self, manager, mock_repo_structure):
        """Test getting package path when package exists"""
        path = manager.get_package_path("testlib")
        expected_path = os.path.join(mock_repo_structure, "github.com", "testuser", "testlib")
        assert path == expected_path
        
        # Test with full path format
        path2 = manager.get_package_path("testuser/testlib")
        assert path2 == expected_path
    
    def test_get_package_path_not_found(self, manager, mock_repo_structure):
        """Test getting package path when package doesn't exist"""
        path = manager.get_package_path("nonexistent")
        assert path is None
    
    def test_get_package_path_no_repo(self, manager):
        """Test getting package path when repository doesn't exist"""
        path = manager.get_package_path("testlib")
        assert path is None
    
    def test_get_docs_no_repo(self, manager):
        """Test getting docs when repository doesn't exist"""
        docs = manager.get_docs()
        assert docs == []
    
    def test_get_docs_content(self, manager, mock_repo_structure, mock_memory_manager):
        """Test getting documentation content"""
        mock_memory_manager.get_libs.return_value = {"testlib": {}, "testlib2": {}}
        
        # Get all docs content
        docs = manager.get_docs(return_paths=False)
        assert len(docs) == 2
        assert "# Test Library" in docs[0]
        assert "# Test Library 2 Documentation" in docs[1]
        
        # Get specific package docs
        specific_docs = manager.get_docs("testlib", return_paths=False)
        assert len(specific_docs) == 1
        assert "# Test Library" in specific_docs[0]
    
    def test_get_docs_paths(self, manager, mock_repo_structure, mock_memory_manager):
        """Test getting documentation paths"""
        mock_memory_manager.get_libs.return_value = {"testlib": {}, "testlib2": {}}
        
        # Get all docs paths
        paths = manager.get_docs(return_paths=True)
        assert len(paths) == 2
        assert all(path.endswith(".md") for path in paths)
        
        # Get specific package paths
        specific_paths = manager.get_docs("testlib", return_paths=True)
        assert len(specific_paths) == 1
        assert specific_paths[0].endswith("README.md")
    
    def test_get_library_docs_paths(self, manager, mock_repo_structure, mock_memory_manager):
        """Test getting library documentation paths"""
        mock_memory_manager.get_libs.return_value = {"testlib": {}}
        
        paths = manager.get_library_docs_paths("testlib")
        assert len(paths) == 1
        assert paths[0].endswith("README.md")
    
    def test_get_library_docs_content(self, manager, mock_repo_structure, mock_memory_manager):
        """Test getting library documentation content"""
        mock_memory_manager.get_libs.return_value = {"testlib": {}}
        
        content = manager.get_library_docs_content("testlib")
        assert len(content) == 1
        assert "# Test Library" in content[0]
    
    @patch('git.Repo')
    def test_clone_repository_success(self, mock_git_repo, manager):
        """Test successful repository cloning"""
        # Repository doesn't exist
        assert not os.path.exists(manager.llm_friendly_packages_dir)
        
        result = manager._clone_repository()
        
        assert result is True
        mock_git_repo.clone_from.assert_called_once()
    
    @patch('git.Repo')
    def test_clone_repository_already_exists(self, mock_git_repo, manager):
        """Test cloning when repository already exists"""
        # Create the repository directory
        os.makedirs(manager.llm_friendly_packages_dir)
        
        result = manager._clone_repository()
        
        assert result is True
        mock_git_repo.clone_from.assert_not_called()
    
    @patch('git.Repo')
    def test_clone_repository_failure(self, mock_git_repo, manager):
        """Test repository cloning failure"""
        from git import GitCommandError
        mock_git_repo.clone_from.side_effect = GitCommandError("clone", "Error")
        
        result = manager._clone_repository()
        
        assert result is False
    
    @patch('git.Repo')
    def test_refresh_repository_success(self, mock_git_repo, manager):
        """Test successful repository refresh"""
        # Create repository directory
        os.makedirs(manager.llm_friendly_packages_dir)
        
        # Mock repository
        mock_repo = Mock()
        mock_origin = Mock()
        mock_origin.url = "https://github.com/allwefantasy/llm_friendly_packages"
        mock_repo.remotes.origin = mock_origin
        mock_git_repo.return_value = mock_repo
        
        result = manager.refresh_repository()
        
        assert result is True
        mock_origin.pull.assert_called_once()
    
    def test_refresh_repository_no_repo(self, manager):
        """Test refreshing when repository doesn't exist"""
        result = manager.refresh_repository()
        assert result is False
    
    @patch('git.Repo')
    def test_refresh_repository_failure(self, mock_git_repo, manager):
        """Test repository refresh failure"""
        from git import GitCommandError
        
        # Create repository directory
        os.makedirs(manager.llm_friendly_packages_dir)
        
        mock_repo = Mock()
        mock_origin = Mock()
        mock_origin.pull.side_effect = GitCommandError("pull", "Error")
        mock_repo.remotes.origin = mock_origin
        mock_git_repo.return_value = mock_repo
        
        result = manager.refresh_repository()
        assert result is False
    
    def test_set_proxy_get_current(self, manager, mock_memory_manager):
        """Test getting current proxy URL"""
        current_proxy = manager.set_proxy()
        expected_url = "https://github.com/allwefantasy/llm_friendly_packages"
        assert current_proxy == expected_url
        mock_memory_manager.get_config.assert_called_with("lib-proxy", expected_url)
    
    def test_set_proxy_new_url(self, manager, mock_memory_manager):
        """Test setting new proxy URL"""
        new_url = "https://custom-proxy.com/repo"
        result = manager.set_proxy(new_url)
        
        assert result == new_url
        mock_memory_manager.set_config.assert_called_once_with("lib-proxy", new_url)
    
    def test_get_repository_info_exists(self, manager, mock_repo_structure):
        """Test getting repository info when it exists"""
        with patch('git.Repo') as mock_git_repo:
            # Mock commit
            mock_commit = Mock()
            mock_commit.committed_datetime.isoformat.return_value = "2023-01-01T12:00:00"
            
            mock_repo = Mock()
            mock_repo.head.commit = mock_commit
            mock_git_repo.return_value = mock_repo
            
            repo_info = manager.get_repository_info()
            
            assert repo_info.exists is True
            assert repo_info.url == "https://github.com/allwefantasy/llm_friendly_packages"
            assert repo_info.last_updated == "2023-01-01T12:00:00"
    
    def test_get_repository_info_not_exists(self, manager):
        """Test getting repository info when it doesn't exist"""
        repo_info = manager.get_repository_info()
        
        assert repo_info.exists is False
        assert repo_info.url == "https://github.com/allwefantasy/llm_friendly_packages"
        assert repo_info.last_updated is None
    
    def test_display_added_libraries_empty(self, manager, capsys):
        """Test displaying empty library list"""
        manager.display_added_libraries()
        captured = capsys.readouterr()
        assert "No libraries added yet" in captured.out
    
    def test_display_added_libraries_with_data(self, manager, mock_memory_manager, capsys):
        """Test displaying library list with data"""
        mock_memory_manager.get_libs.return_value = {"numpy": {}, "pandas": {}}
        
        manager.display_added_libraries()
        captured = capsys.readouterr()
        # Console output includes library names in the table
        assert "numpy" in captured.out or "pandas" in captured.out
    
    def test_display_all_libraries_no_repo(self, manager, capsys):
        """Test displaying all libraries when repository doesn't exist"""
        manager.display_all_libraries()
        captured = capsys.readouterr()
        assert "repository does not exist" in captured.out
    
    def test_display_library_docs_no_docs(self, manager, capsys):
        """Test displaying library docs when none exist"""
        manager.display_library_docs("nonexistent")
        captured = capsys.readouterr()
        assert "No markdown files found" in captured.out


class TestDataModels:
    """Test suite for data models"""
    
    def test_library_info_creation(self):
        """Test LibraryInfo creation"""
        lib_info = LibraryInfo(
            domain="github.com",
            username="testuser",
            lib_name="testlib",
            full_path="testuser/testlib",
            is_added=True,
            has_md_files=True
        )
        
        assert lib_info.domain == "github.com"
        assert lib_info.username == "testuser"
        assert lib_info.lib_name == "testlib"
        assert lib_info.full_path == "testuser/testlib"
        assert lib_info.is_added is True
        assert lib_info.has_md_files is True
    
    def test_library_info_defaults(self):
        """Test LibraryInfo default values"""
        lib_info = LibraryInfo(
            domain="github.com",
            username="testuser",
            lib_name="testlib",
            full_path="testuser/testlib",
            is_added=False
        )
        
        assert lib_info.has_md_files is True  # Default value
    
    def test_package_doc_creation(self):
        """Test PackageDoc creation"""
        doc = PackageDoc(
            file_path="/path/to/doc.md",
            content="# Documentation"
        )
        
        assert doc.file_path == "/path/to/doc.md"
        assert doc.content == "# Documentation"
    
    def test_package_doc_no_content(self):
        """Test PackageDoc without content"""
        doc = PackageDoc(file_path="/path/to/doc.md")
        
        assert doc.file_path == "/path/to/doc.md"
        assert doc.content is None
    
    def test_repository_info_creation(self):
        """Test RepositoryInfo creation"""
        repo_info = RepositoryInfo(
            exists=True,
            url="https://github.com/test/repo",
            last_updated="2023-01-01T12:00:00"
        )
        
        assert repo_info.exists is True
        assert repo_info.url == "https://github.com/test/repo"
        assert repo_info.last_updated == "2023-01-01T12:00:00"
    
    def test_repository_info_defaults(self):
        """Test RepositoryInfo default values"""
        repo_info = RepositoryInfo(
            exists=False,
            url="https://github.com/test/repo"
        )
        
        assert repo_info.exists is False
        assert repo_info.url == "https://github.com/test/repo"
        assert repo_info.last_updated is None


class TestIntegration:
    """Integration tests"""
    
    @pytest.fixture
    def real_temp_project(self):
        """Create a real temporary project for integration testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_workflow_with_mocked_git(self, real_temp_project):
        """Test a complete workflow with mocked git operations"""
        with patch('git.Repo') as mock_git_repo:
            # Create manager
            manager = LLMFriendlyPackageManager(real_temp_project)
            
            # Add a library (this will trigger repository cloning)
            result = manager.add_library("test-library")
            assert result is True
            
            # Check that library is added
            assert manager.has_library("test-library")
            libs = manager.list_added_libraries()
            assert "test-library" in libs
            
            # Remove the library
            result = manager.remove_library("test-library")
            assert result is True
            assert not manager.has_library("test-library")
    
    def test_error_handling_in_docs_reading(self, real_temp_project):
        """Test error handling when reading documentation files"""
        manager = LLMFriendlyPackageManager(real_temp_project)
        
        # Create a corrupted file structure
        repo_dir = manager.llm_friendly_packages_dir
        os.makedirs(repo_dir, exist_ok=True)
        
        test_lib_path = os.path.join(repo_dir, "github.com", "testuser", "testlib")
        os.makedirs(test_lib_path, exist_ok=True)
        
        # Create a file with permission issues (simulate by creating a directory with same name)
        bad_file_path = os.path.join(test_lib_path, "README.md")
        os.makedirs(bad_file_path, exist_ok=True)  # This will cause read error
        
        # Add the library
        manager.add_library("testlib")
        
        # Try to read docs - should handle the error gracefully
        docs = manager.get_library_docs_content("testlib")
        assert docs == []  # Should return empty list on error


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"]) 