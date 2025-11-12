"""
Tests for specific linter implementations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from pathlib import Path

from autocoder.common.linter_core.linters.python_linter import PythonLinter
from autocoder.common.linter_core.linters.typescript_linter import TypeScriptLinter
from autocoder.common.linter_core.models.lint_result import LintResult


class TestPythonLinter:
    """Test cases for PythonLinter."""
    
    @pytest.fixture
    def python_linter(self):
        """Create a PythonLinter instance."""
        return PythonLinter()
    
    def test_init_default_config(self):
        """Test PythonLinter initialization with default config."""
        linter = PythonLinter()
        assert linter.use_mypy is True
        assert linter.flake8_args == []
        assert linter.mypy_args == []
        assert linter.flake8_timeout_secs == 30
        assert linter.mypy_timeout_secs == 30
    
    def test_init_custom_config(self):
        """Test PythonLinter initialization with custom config."""
        config = {
            'use_mypy': False,
            'flake8_args': ['--max-line-length=120'],
            'mypy_args': ['--strict'],
            'flake8_timeout': 60,
            'mypy_timeout': 45
        }
        linter = PythonLinter(config)
        assert linter.use_mypy is False
        assert linter.flake8_args == ['--max-line-length=120']
        assert linter.mypy_args == ['--strict']
        assert linter.flake8_timeout_secs == 60
        assert linter.mypy_timeout_secs == 45
    
    def test_supported_extensions(self, python_linter):
        """Test supported file extensions."""
        assert python_linter.supported_extensions == ['.py', '.pyx', '.pyi']
    
    def test_language_name(self, python_linter):
        """Test language name property."""
        assert python_linter.language_name == "Python"
    
    @patch('subprocess.run')
    def test_is_available_true(self, mock_run, python_linter):
        """Test is_available when flake8 is installed."""
        mock_run.return_value = MagicMock(returncode=0)
        assert python_linter.is_available() is True
        mock_run.assert_called_once_with(
            ['flake8', '--version'], 
            capture_output=True, 
            check=True, 
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_is_available_false(self, mock_run, python_linter):
        """Test is_available when flake8 is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert python_linter.is_available() is False
    
    @patch('subprocess.run')
    def test_lint_file_flake8_only(self, mock_run):
        """Test linting a file with only flake8."""
        # Setup
        linter = PythonLinter({'use_mypy': False})
        mock_run.return_value = MagicMock(
            stdout="test.py:1:1: E302 expected 2 blank lines, found 1",
            stderr=""
        )
        
        # Execute
        result = linter.lint_file('test.py')
        
        # Verify
        assert result.linter_name == "PythonLinter"
        assert result.file_name == "test.py"
        assert "=== flake8 ===" in result.lint_result
        assert "E302 expected 2 blank lines" in result.lint_result
        assert result.metadata['mypy_enabled'] is False
        assert result.metadata['tools_used'] == ['flake8']
    
    @patch('subprocess.run')
    def test_lint_file_with_mypy(self, mock_run):
        """Test linting a file with both flake8 and mypy."""
        # Setup
        linter = PythonLinter({'use_mypy': True})
        
        # Mock flake8 and mypy calls
        mock_run.side_effect = [
            # flake8 call
            MagicMock(stdout="test.py:1:1: E302 expected 2 blank lines", stderr=""),
            # mypy availability check
            MagicMock(returncode=0),
            # mypy call
            MagicMock(stdout="test.py:5: error: Name 'foo' is not defined", stderr="")
        ]
        
        # Execute
        result = linter.lint_file('test.py')
        
        # Verify
        assert "=== flake8 ===" in result.lint_result
        assert "=== mypy ===" in result.lint_result
        assert "E302 expected 2 blank lines" in result.lint_result
        assert "Name 'foo' is not defined" in result.lint_result
        assert result.metadata['mypy_enabled'] is True
        assert result.metadata['tools_used'] == ['flake8', 'mypy']
    
    @patch('subprocess.run')
    def test_lint_file_timeout(self, mock_run):
        """Test handling of timeout during linting."""
        linter = PythonLinter()
        mock_run.side_effect = subprocess.TimeoutExpired(['flake8'], 30)
        
        result = linter.lint_file('test.py')
        assert "Error: flake8 execution timed out" in result.lint_result
        assert result.metadata.get('error') is True


class TestTypeScriptLinter:
    """Test cases for TypeScriptLinter."""
    
    @pytest.fixture
    def ts_linter(self):
        """Create a TypeScriptLinter instance."""
        return TypeScriptLinter()
    
    def test_init_default_config(self):
        """Test TypeScriptLinter initialization with default config."""
        linter = TypeScriptLinter()
        assert linter.use_eslint is True
        assert linter.tsc_args == ['--noEmit', '--strict']
        assert linter.eslint_args == []
        assert linter.tsconfig_path is None
        assert linter.tsc_timeout_secs == 60
        assert linter.eslint_timeout_secs == 30
    
    def test_init_custom_config(self):
        """Test TypeScriptLinter initialization with custom config."""
        config = {
            'use_eslint': False,
            'tsc_args': ['--noEmit'],
            'eslint_args': ['--fix'],
            'tsconfig_path': './tsconfig.json',
            'tsc_timeout': 90,
            'eslint_timeout': 45
        }
        linter = TypeScriptLinter(config)
        assert linter.use_eslint is False
        assert linter.tsc_args == ['--noEmit']
        assert linter.eslint_args == ['--fix']
        assert linter.tsconfig_path == './tsconfig.json'
        assert linter.tsc_timeout_secs == 90
        assert linter.eslint_timeout_secs == 45
    
    def test_supported_extensions(self, ts_linter):
        """Test supported file extensions."""
        assert ts_linter.supported_extensions == ['.ts', '.tsx', '.js', '.jsx']
    
    def test_language_name(self, ts_linter):
        """Test language name property."""
        assert ts_linter.language_name == "TypeScript"
    
    @patch('subprocess.run')
    def test_is_available_true(self, mock_run, ts_linter):
        """Test is_available when tsc is installed."""
        mock_run.return_value = MagicMock(returncode=0)
        assert ts_linter.is_available() is True
        mock_run.assert_called_once_with(
            ['tsc', '--version'], 
            capture_output=True, 
            check=True, 
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_is_available_false(self, mock_run, ts_linter):
        """Test is_available when tsc is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert ts_linter.is_available() is False
    
    @patch('subprocess.run')
    @patch('time.time')
    def test_lint_file_tsc_only(self, mock_time, mock_run):
        """Test linting a file with only tsc."""
        # Setup
        mock_time.side_effect = [0, 1]  # Start and end time
        linter = TypeScriptLinter({'use_eslint': False})
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="test.ts(1,5): error TS2322: Type 'string' is not assignable to type 'number'."
        )
        
        # Execute
        result = linter.lint_file('test.ts')
        
        # Verify
        assert result.linter_name == "TypeScriptLinter"
        assert len(result.files_checked) == 1
        assert 'test.ts' in result.files_checked[0]
        assert result.has_issues
        assert "=== tsc ===" in result.lint_output
        assert "Type 'string' is not assignable" in result.lint_output
        assert result.metadata['eslint_enabled'] is False
        assert result.metadata['tools_used'] == ['tsc']
        assert result.execution_time == 1
    
    @patch('subprocess.run')
    @patch('time.time')
    def test_lint_file_with_eslint(self, mock_time, mock_run):
        """Test linting a file with both tsc and eslint."""
        # Setup
        mock_time.side_effect = [0, 2]  # Start and end time
        linter = TypeScriptLinter({'use_eslint': True})
        
        # Mock tsc and eslint calls
        mock_run.side_effect = [
            # tsc call
            MagicMock(stdout="", stderr="test.ts(1,5): error TS2322: Type error"),
            # eslint availability check
            MagicMock(returncode=0),
            # eslint call
            MagicMock(stdout="test.ts:2:10 warning Missing semicolon", stderr="")
        ]
        
        # Execute
        result = linter.lint_file('test.ts')
        
        # Verify
        assert result.has_issues
        assert "=== tsc ===" in result.lint_output
        assert "=== eslint ===" in result.lint_output
        assert "Type error" in result.lint_output
        assert "Missing semicolon" in result.lint_output
        assert result.metadata['eslint_enabled'] is True
        assert result.metadata['tools_used'] == ['tsc', 'eslint']
    
    @patch('subprocess.run')
    def test_lint_file_with_tsconfig(self, mock_run):
        """Test linting with custom tsconfig path."""
        linter = TypeScriptLinter({
            'tsconfig_path': './custom-tsconfig.json',
            'use_eslint': False  # Disable eslint to test only tsc
        })
        mock_run.return_value = MagicMock(stdout="", stderr="")
        
        linter.lint_file('test.ts')
        
        # Verify tsc was called with --project argument
        call_args = mock_run.call_args[0][0]
        assert '--project' in call_args
        assert './custom-tsconfig.json' in call_args
