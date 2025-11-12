"""
Tests for linter factory and manager components.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from autocoder.common.linter_core.linter_factory import LinterFactory
from autocoder.common.linter_core.linter_manager import LinterManager
from autocoder.common.linter_core.models.lint_result import LintResult
from autocoder.common.linter_core.linters.python_linter import PythonLinter
from autocoder.common.linter_core.linters.typescript_linter import TypeScriptLinter


class TestLinterFactory:
    """Test cases for LinterFactory."""
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = LinterFactory.get_supported_languages()
        assert isinstance(languages, list)
        assert 'python' in languages
        assert 'typescript' in languages
        assert 'java' in languages
    
    def test_get_supported_extensions(self):
        """Test getting supported file extensions."""
        extensions = LinterFactory.get_supported_extensions()
        assert isinstance(extensions, list)
        assert '.py' in extensions
        assert '.ts' in extensions
        assert '.tsx' in extensions
        assert '.java' in extensions
    
    def test_create_linter_python(self):
        """Test creating Python linter."""
        linter = LinterFactory.create_linter('python')
        assert isinstance(linter, PythonLinter)
        assert linter.language_name == "Python"
    
    def test_create_linter_typescript(self):
        """Test creating TypeScript linter."""
        linter = LinterFactory.create_linter('typescript')
        assert isinstance(linter, TypeScriptLinter)
        assert linter.language_name == "TypeScript"
    
    def test_create_linter_with_config(self):
        """Test creating linter with custom config."""
        config = {'use_mypy': False}
        linter = LinterFactory.create_linter('python', config)
        assert isinstance(linter, PythonLinter)
        assert linter.use_mypy is False
    
    def test_create_linter_unsupported(self):
        """Test creating linter for unsupported language."""
        linter = LinterFactory.create_linter('unsupported')
        assert linter is None
    
    def test_create_linter_for_file_python(self):
        """Test creating linter for Python file."""
        linter = LinterFactory.create_linter_for_file('test.py')
        assert isinstance(linter, PythonLinter)
    
    def test_create_linter_for_file_typescript(self):
        """Test creating linter for TypeScript file."""
        linter = LinterFactory.create_linter_for_file('test.ts')
        assert isinstance(linter, TypeScriptLinter)
    
    def test_create_linter_for_file_java(self):
        """Test creating linter for Java file."""
        from autocoder.common.linter_core.linters.java_linter import JavaLinter
        linter = LinterFactory.create_linter_for_file('Test.java')
        assert isinstance(linter, JavaLinter)
    
    def test_create_linter_for_file_unsupported(self):
        """Test creating linter for unsupported file."""
        linter = LinterFactory.create_linter_for_file('test.txt')
        assert linter is None
    
    def test_is_file_supported_true(self):
        """Test checking if file is supported."""
        assert LinterFactory.is_file_supported('test.py') is True
        assert LinterFactory.is_file_supported('test.ts') is True
        assert LinterFactory.is_file_supported('test.tsx') is True
    
    def test_is_file_supported_false(self):
        """Test checking if file is not supported."""
        assert LinterFactory.is_file_supported('test.txt') is False
        assert LinterFactory.is_file_supported('test.md') is False


class TestLinterManager:
    """Test cases for LinterManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a linter manager instance."""
        return LinterManager()
    
    @pytest.fixture
    def mock_linter(self):
        """Create a mock linter."""
        linter = Mock()
        linter.name = "MockLinter"
        linter.supported_extensions = ['.mock']
        linter.is_available.return_value = True
        return linter
    
    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert isinstance(manager, LinterManager)
        assert hasattr(manager, 'linters')
        assert hasattr(manager, 'max_workers')
        assert hasattr(manager, 'timeout')
    
    def test_manager_with_config(self):
        """Test manager with custom config."""
        config = {
            'max_workers': 8,
            'timeout': 600,
            'python_config': {'use_mypy': False}
        }
        manager = LinterManager(config)
        assert manager.max_workers == 8
        assert manager.timeout == 600
    
    def test_get_available_linters(self, manager):
        """Test getting available linters."""
        available = manager.get_available_linters()
        assert isinstance(available, dict)
    
    def test_add_custom_linter(self, manager, mock_linter):
        """Test adding custom linter."""
        manager.add_linter('mock', mock_linter)
        assert 'mock' in manager.linters
        assert manager.linters['mock'] == mock_linter
    
    def test_remove_linter(self, manager, mock_linter):
        """Test removing linter."""
        manager.add_linter('mock', mock_linter)
        manager.remove_linter('mock')
        assert 'mock' not in manager.linters
    
    def test_lint_file_not_found(self, manager):
        """Test linting non-existent file."""
        result = manager.lint_file('nonexistent.py')
        assert isinstance(result, LintResult)
        assert result.success is False
        assert "File not found" in result.error_message
    
    @patch('pathlib.Path.exists')
    def test_lint_file_no_linter(self, mock_exists, manager):
        """Test linting file with no available linter."""
        mock_exists.return_value = True
        result = manager.lint_file('test.unsupported')
        assert isinstance(result, LintResult)
        assert result.success is False
        assert "No available linter" in result.error_message
    
    def test_lint_files_empty(self, manager):
        """Test linting empty file list."""
        results = manager.lint_files([])
        assert isinstance(results, dict)
        assert len(results) == 0
    
    def test_get_summary_report_empty(self, manager):
        """Test summary report for empty results."""
        summary = manager.get_summary_report({})
        assert summary['total_files'] == 0
        assert summary['successful_files'] == 0
        assert summary['failed_files'] == 0
        assert summary['total_issues'] == 0
    
    def test_get_summary_report_with_results(self, manager):
        """Test summary report with results."""
        results = {
            'file1.py': LintResult(
                linter_name='TestLinter',
                files_checked=['file1.py'],
                success=True,
                execution_time=1.0
            ),
            'file2.py': LintResult(
                linter_name='TestLinter',
                files_checked=['file2.py'],
                success=False,
                execution_time=0.5
            )
        }
        
        summary = manager.get_summary_report(results)
        assert summary['total_files'] == 2
        assert summary['successful_files'] == 1
        assert summary['failed_files'] == 1
        assert summary['total_execution_time'] == 1.0  # Only successful files counted
    
    def test_lint_output_filtering(self, manager):
        """Test filtering based on lint output content."""
        # Create test results with different lint outputs
        result1 = LintResult(
            linter_name='TestLinter',
            files_checked=['test1.py'],
            lint_output='test1.py:1:1: E301 expected 1 blank line, found 0'
        )
        result2 = LintResult(
            linter_name='TestLinter',
            files_checked=['test2.py'],
            lint_output='test2.py:2:1: W291 trailing whitespace'
        )
        
        results = {'test1.py': result1, 'test2.py': result2}
        
        # Test that results with lint output are correctly identified
        files_with_issues = [
            path for path, result in results.items() 
            if result.has_issues
        ]
        
        assert len(files_with_issues) == 2
        assert 'test1.py' in files_with_issues
        assert 'test2.py' in files_with_issues
    
    def test_format_results(self, manager):
        """Test formatting results."""
        result = LintResult(
            linter_name='TestLinter',
            files_checked=['test.py']
        )
        results = {'test.py': result}
        
        formatted = manager.format_results(results)
        assert isinstance(formatted, dict)
        assert 'test.py' in formatted
