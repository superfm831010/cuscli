
"""
Integration tests for the linter core module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from autocoder.common.linter_core import LinterManager, LinterFactory
from autocoder.common.linter_core.models.lint_result import LintResult


class TestIntegration:
    """Integration tests with temporary project files."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def python_file(self, temp_dir):
        """Create a temporary Python file."""
        python_content = '''
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
        python_file = temp_dir / "test.py"
        python_file.write_text(python_content)
        return python_file
    
    @pytest.fixture
    def typescript_file(self, temp_dir):
        """Create a temporary TypeScript file."""
        ts_content = '''
function greet(name: string): string {
    return `Hello, ${name}!`;
}

export { greet };
'''
        ts_file = temp_dir / "test.ts"
        ts_file.write_text(ts_content)
        return ts_file
    
    @pytest.fixture
    def mixed_project(self, temp_dir):
        """Create a mixed project with multiple file types."""
        # Python file
        py_content = '''
def calculate(x, y):
    return x + y
'''
        (temp_dir / "calculator.py").write_text(py_content)
        
        # TypeScript file
        ts_content = '''
interface User {
    name: string;
    age: number;
}

function createUser(name: string, age: number): User {
    return { name, age };
}
'''
        (temp_dir / "user.ts").write_text(ts_content)
        
        # Java file
        java_content = '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''
        (temp_dir / "HelloWorld.java").write_text(java_content)
        
        # Unsupported file
        (temp_dir / "readme.txt").write_text("This is a readme file.")
        
        return temp_dir
    
    def test_factory_creates_appropriate_linters(self):
        """Test that factory creates correct linters for different languages."""
        python_linter = LinterFactory.create_linter('python')
        typescript_linter = LinterFactory.create_linter('typescript')
        java_linter = LinterFactory.create_linter('java')
        
        assert python_linter is not None
        assert typescript_linter is not None
        assert java_linter is not None
        assert python_linter.language_name == "Python"
        assert typescript_linter.language_name == "TypeScript"
        assert java_linter.language_name == "Java"
    
    def test_factory_file_detection(self, python_file, typescript_file):
        """Test that factory correctly detects file types."""
        python_linter = LinterFactory.create_linter_for_file(python_file)
        typescript_linter = LinterFactory.create_linter_for_file(typescript_file)
        
        assert python_linter is not None
        assert typescript_linter is not None
        assert python_linter.language_name == "Python"
        assert typescript_linter.language_name == "TypeScript"
    
    @patch('subprocess.run')
    def test_manager_lint_single_file(self, mock_run, python_file):
        """Test manager linting a single file."""
        # Mock flake8 output
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        manager = LinterManager()
        result = manager.lint_file(python_file)
        
        assert isinstance(result, LintResult)
        assert result.linter_name == "PythonLinter"
        assert str(python_file) in result.files_checked
    
    @patch('subprocess.run')
    def test_manager_lint_directory(self, mock_run, mixed_project):
        """Test manager linting an entire directory."""
        # Mock subprocess calls
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        manager = LinterManager()
        results = manager.lint_directory(mixed_project)
        
        assert isinstance(results, dict)
        # Should have results for .py, .ts, and .java files, but not .txt
        assert len(results) >= 3
        
        # Check that we have results for supported files
        py_files = [path for path in results.keys() if path.endswith('.py')]
        ts_files = [path for path in results.keys() if path.endswith('.ts')]
        java_files = [path for path in results.keys() if path.endswith('.java')]
        
        assert len(py_files) >= 1
        assert len(ts_files) >= 1
        assert len(java_files) >= 1
    
    @patch('subprocess.run')
    def test_manager_parallel_processing(self, mock_run, mixed_project):
        """Test manager with parallel processing."""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        manager = LinterManager({'max_workers': 2})
        results = manager.lint_directory(mixed_project, parallel=True)
        
        assert isinstance(results, dict)
        assert len(results) >= 2
    
    @patch('subprocess.run')
    def test_manager_sequential_processing(self, mock_run, mixed_project):
        """Test manager with sequential processing."""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        manager = LinterManager()
        results = manager.lint_directory(mixed_project, parallel=False)
        
        assert isinstance(results, dict)
        assert len(results) >= 2
    
    @patch('subprocess.run')
    def test_manager_include_exclude_patterns(self, mock_run, mixed_project):
        """Test manager with include/exclude patterns."""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        manager = LinterManager()
        
        # Test include pattern - only Python files
        results = manager.lint_directory(
            mixed_project, 
            include_patterns=['*.py']
        )
        
        py_files = [path for path in results.keys() if path.endswith('.py')]
        ts_files = [path for path in results.keys() if path.endswith('.ts')]
        
        assert len(py_files) >= 1
        assert len(ts_files) == 0
    
    def test_manager_summary_report(self):
        """Test manager summary report generation."""
        manager = LinterManager()
        
        # Create mock results
        results = {
            'file1.py': LintResult(
                linter_name='PythonLinter',
                files_checked=['file1.py'],
                success=True,
                execution_time=1.0
            ),
            'file2.ts': LintResult(
                linter_name='TypeScriptLinter',
                files_checked=['file2.ts'],
                success=True,
                execution_time=1.5
            ),
            'file3.py': LintResult(
                linter_name='PythonLinter',
                files_checked=['file3.py'],
                success=False,
                execution_time=0.0
            )
        }
        
        summary = manager.get_summary_report(results)
        
        assert summary['total_files'] == 3
        assert summary['successful_files'] == 2
        assert summary['failed_files'] == 1
        assert summary['total_execution_time'] == 2.5
        assert summary['average_execution_time'] == 1.25
    
    @patch('subprocess.run')
    def test_end_to_end_workflow(self, mock_run, mixed_project):
        """Test complete end-to-end workflow."""
        # Mock subprocess calls with some lint output
        mock_run.return_value = MagicMock(
            stdout="test.py:1:1: E302 expected 2 blank lines",
            stderr="",
            returncode=1
        )
        
        # Initialize manager
        manager = LinterManager({
            'max_workers': 2,
            'timeout': 60,
            'python_config': {'use_mypy': False}
        })
        
        # Lint directory
        results = manager.lint_directory(mixed_project, recursive=True)
        
        # Generate summary
        summary = manager.get_summary_report(results)
        
        # Format results
        formatted = manager.format_results(results)
        
        # Assertions
        assert isinstance(results, dict)
        assert isinstance(summary, dict)
        assert isinstance(formatted, dict)
        assert summary['total_files'] >= 2
        assert len(formatted) == len(results)
    
    def test_linter_availability_check(self):
        """Test checking linter availability."""
        manager = LinterManager()
        available = manager.get_available_linters()
        
        assert isinstance(available, dict)
        # The dictionary should contain linter availability status
        # Note: In test environment, linters may not be available
        # but the structure should be correct
        for language, is_available in available.items():
            assert isinstance(is_available, bool)
    
    def test_error_handling_integration(self, python_file):
        """Test error handling in integration scenario."""
        # Create manager first, then patch the specific linter's lint_file method
        manager = LinterManager()
        
        # Mock a linter to raise exception during linting
        with patch.object(manager, '_get_linter_for_file') as mock_get_linter:
            mock_linter = Mock()
            mock_linter.lint_file.side_effect = Exception("Tool not found")
            mock_get_linter.return_value = mock_linter
            
            result = manager.lint_file(python_file)
            
            assert isinstance(result, LintResult)
            assert result.success is False
            assert "Tool not found" in result.error_message
    
    def test_configuration_propagation(self):
        """Test that configuration is properly propagated."""
        config = {
            'max_workers': 8,
            'timeout': 120,
            'python_config': {
                'use_mypy': False,
                'flake8_args': ['--max-line-length=120']
            },
            'typescript_config': {
                'use_eslint': False,
                'tsc_args': ['--strict']
            }
        }
        
        manager = LinterManager(config)
        
        assert manager.max_workers == 8
        assert manager.timeout == 120
        
        # Check that linter configs are applied
        if 'python' in manager.linters:
            python_linter = manager.linters['python']
            assert python_linter.use_mypy is False
            assert '--max-line-length=120' in python_linter.flake8_args
        
        if 'typescript' in manager.linters:
            ts_linter = manager.linters['typescript']
            assert ts_linter.use_eslint is False
            assert '--strict' in ts_linter.tsc_args

