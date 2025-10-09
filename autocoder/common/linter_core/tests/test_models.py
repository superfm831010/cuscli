"""
Tests for lint result models.
"""

import pytest
from autocoder.common.linter_core.models.lint_result import LintResult


class TestLintResult:
    """Test cases for LintResult model."""
    
    def test_lint_result_creation(self):
        """Test creating a LintResult instance."""
        result = LintResult(
            linter_name="TestLinter",
            files_checked=["test.py"],
            metadata={"key": "value"}
        )
        # Set lint_result using property for backward compatibility
        result.lint_result = "Some lint output"
        
        assert result.linter_name == "TestLinter"
        assert result.file_name == "test.py"
        assert result.lint_result == "Some lint output"
        assert result.metadata == {"key": "value"}
    
    def test_lint_result_defaults(self):
        """Test LintResult with default values."""
        result = LintResult(
            linter_name="TestLinter",
            files_checked=["test.py"]
        )
        
        assert result.lint_result == ""
        assert result.metadata == {}
    
    def test_to_dict(self):
        """Test converting LintResult to dictionary."""
        result = LintResult(
            linter_name="TestLinter",
            files_checked=["test.py"],
            metadata={"tool": "flake8"}
        )
        result.lint_result = "Lint output"
        
        data = result.to_dict()
        expected_keys = {
            'linter_name', 'files_checked', 'lint_output', 'execution_time',
            'success', 'error_message', 'metadata', 'file_name', 'lint_result'
        }
        assert set(data.keys()) == expected_keys
        assert data['linter_name'] == 'TestLinter'
        assert data['file_name'] == 'test.py'
        assert data['lint_result'] == 'Lint output'
        assert data['metadata'] == {'tool': 'flake8'}
    
    def test_from_dict(self):
        """Test creating LintResult from dictionary."""
        data = {
            'linter_name': 'TestLinter',
            'file_name': 'test.py',
            'lint_result': 'Lint output',
            'metadata': {'tool': 'mypy'}
        }
        
        result = LintResult.from_dict(data)
        assert result.linter_name == "TestLinter"
        assert result.file_name == "test.py"
        assert result.lint_result == "Lint output"
        assert result.metadata == {"tool": "mypy"}
    
    def test_from_dict_missing_fields(self):
        """Test creating LintResult from incomplete dictionary."""
        data = {
            'linter_name': 'TestLinter',
            'file_name': 'test.py'
        }
        
        result = LintResult.from_dict(data)
        assert result.lint_result == ""
        assert result.metadata == {}