"""
Tests for linter output formatters.
"""

import pytest
from typing import Dict, Any

from autocoder.common.linter_core.formatters.base_formatter import BaseLintOutputFormatter
from autocoder.common.linter_core.formatters.raw_formatter import RawLintOutputFormatter
from autocoder.common.linter_core.models.lint_result import LintResult


class CustomTestFormatter(BaseLintOutputFormatter):
    """Test implementation of formatter for testing abstract base class."""
    
    def format_result(self, result: LintResult) -> str:
        """Format as a simple string."""
        return f"{result.linter_name}: {result.file_name} - {result.lint_result}"
    
    def format_results(self, results: Dict[str, LintResult]) -> str:
        """Override to return concatenated string."""
        lines = []
        for path, result in results.items():
            lines.append(f"{path}: {self.format_result(result)}")
        return "\n".join(lines)


class TestBaseLintOutputFormatter:
    """Test the base formatter abstract class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            BaseLintOutputFormatter()
    
    def test_custom_implementation(self):
        """Test custom formatter implementation."""
        formatter = CustomTestFormatter()
        result = LintResult(
            linter_name="TestLinter",
            files_checked=["test.py"]
        )
        result.lint_result = "No issues found"
        
        formatted = formatter.format_result(result)
        assert formatted == "TestLinter: test.py - No issues found"
    
    def test_format_results_default_behavior(self):
        """Test default format_results implementation."""
        formatter = CustomTestFormatter()
        result1 = LintResult(
            linter_name="Linter1",
            files_checked=["file1.py"]
        )
        result1.lint_result = "Issue 1"
        
        result2 = LintResult(
            linter_name="Linter2",
            files_checked=["file2.py"]
        )
        result2.lint_result = "Issue 2"
        
        results = {
            "file1.py": result1,
            "file2.py": result2
        }
        
        formatted = formatter.format_results(results)
        assert "file1.py: Linter1: file1.py - Issue 1" in formatted
        assert "file2.py: Linter2: file2.py - Issue 2" in formatted


class TestRawLintOutputFormatter:
    """Test the raw formatter implementation."""
    
    @pytest.fixture
    def formatter(self):
        """Create a raw formatter instance."""
        return RawLintOutputFormatter()
    
    @pytest.fixture
    def sample_result(self):
        """Create a sample lint result."""
        result = LintResult(
            linter_name="PythonLinter",
            files_checked=["example.py"],
            metadata={"tool": "flake8", "severity": "error"}
        )
        result.lint_result = "line 10: undefined variable"
        return result
    
    def test_format_result_returns_dict(self, formatter, sample_result):
        """Test that format_result returns a dictionary."""
        formatted = formatter.format_result(sample_result)
        
        assert isinstance(formatted, dict)
        assert formatted["linter_name"] == "PythonLinter"
        assert formatted["file_name"] == "example.py"
        assert formatted["lint_result"] == "line 10: undefined variable"
        assert formatted["metadata"]["tool"] == "flake8"
    
    def test_format_results_returns_dict_of_dicts(self, formatter):
        """Test formatting multiple results."""
        result1 = LintResult(
            linter_name="Linter1",
            files_checked=["file1.py"],
            metadata={"line": 5}
        )
        result1.lint_result = "Issue 1"
        
        result2 = LintResult(
            linter_name="Linter2",
            files_checked=["file2.py"],
            metadata={"line": 10}
        )
        result2.lint_result = "Issue 2"
        
        results = {
            "file1.py": result1,
            "file2.py": result2
        }
        
        formatted = formatter.format_results(results)
        
        assert isinstance(formatted, dict)
        assert len(formatted) == 2
        assert "file1.py" in formatted
        assert "file2.py" in formatted
        assert formatted["file1.py"]["lint_result"] == "Issue 1"
        assert formatted["file2.py"]["metadata"]["line"] == 10
    
    def test_empty_results(self, formatter):
        """Test formatting empty results."""
        formatted = formatter.format_results({})
        assert formatted == {}
    
    def test_result_with_empty_metadata(self, formatter):
        """Test result with no metadata."""
        result = LintResult(
            linter_name="TestLinter",
            files_checked=["test.py"]
        )
        
        formatted = formatter.format_result(result)
        assert formatted["metadata"] == {}
        assert formatted["lint_result"] == ""
