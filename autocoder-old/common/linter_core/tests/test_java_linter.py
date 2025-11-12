"""
Tests for Java linter implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import platform
import tempfile
import os
from pathlib import Path

from autocoder.common.linter_core.linters.java_linter import JavaLinter
from autocoder.common.linter_core.models.lint_result import LintResult


class TestJavaLinter:
    """Test cases for JavaLinter."""
    
    @pytest.fixture
    def java_linter(self):
        """Create a JavaLinter instance."""
        return JavaLinter()
    
    def test_init_default_config(self):
        """Test JavaLinter initialization with default config."""
        linter = JavaLinter()
        assert linter.javac_args == []
        assert linter.javac_timeout_secs == 30
    
    def test_init_custom_config(self):
        """Test JavaLinter initialization with custom config."""
        config = {
            'javac_args': ['-Xlint:all'],
            'javac_timeout': 60
        }
        linter = JavaLinter(config)
        assert linter.javac_args == ['-Xlint:all']
        assert linter.javac_timeout_secs == 60
    
    def test_supported_extensions(self, java_linter):
        """Test supported file extensions."""
        assert java_linter.supported_extensions == ['.java']
    
    def test_language_name(self, java_linter):
        """Test language name property."""
        assert java_linter.language_name == "Java"
    
    @patch('subprocess.run')
    def test_is_available_true(self, mock_run, java_linter):
        """Test is_available when javac is installed."""
        mock_run.return_value = MagicMock(returncode=0)
        assert java_linter.is_available() is True
        mock_run.assert_called_once_with(
            ['javac', '-version'], 
            capture_output=True, 
            check=True, 
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_is_available_false(self, mock_run, java_linter):
        """Test is_available when javac is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert java_linter.is_available() is False
    
    @patch('subprocess.run')
    @patch('time.time')
    def test_lint_file_no_errors(self, mock_time, mock_run):
        """Test linting a file with no errors."""
        # Setup
        mock_time.side_effect = [0, 1]  # Start and end time
        linter = JavaLinter()
        mock_run.return_value = MagicMock(
            stdout="",
            stderr=""  # No errors
        )
        
        # Execute
        result = linter.lint_file('Test.java')
        
        # Verify
        assert result.linter_name == "JavaLinter"
        assert len(result.files_checked) == 1
        assert 'Test.java' in result.files_checked[0]
        assert not result.has_issues  # No output means no issues
        assert result.metadata['tools_used'] == ['javac']
        assert result.execution_time == 1
        assert result.success is True
    
    @patch('subprocess.run')
    @patch('time.time')
    @patch('platform.system')
    def test_lint_file_with_errors_unix(self, mock_platform, mock_time, mock_run):
        """Test linting a file with syntax errors on Unix."""
        # Setup
        mock_platform.return_value = 'Linux'
        mock_time.side_effect = [0, 1.5]
        linter = JavaLinter()
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Test.java:5: error: ';' expected\n    int x = 10\n              ^\n1 error"
        )
        
        # Execute
        result = linter.lint_file('Test.java')
        
        # Verify
        assert result.has_issues
        assert "=== javac ===" in result.lint_output
        assert "';' expected" in result.lint_output
        assert result.metadata['tools_used'] == ['javac']
        assert result.success is True
        
        # Check the command used (should have javac, -d, temp_dir, --release, 8, -Xlint:all, -proc:none, Test.java)
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'javac'
        assert call_args[1] == '-d'
        # call_args[2] will be the temporary directory path
        assert call_args[3] == '--release'
        assert call_args[4] == '8'
        assert call_args[5] == '-Xlint:all'
        assert call_args[6] == '-proc:none'
        assert call_args[-1] == 'Test.java'  # File path is last
    
    @patch('subprocess.run')
    @patch('time.time')
    @patch('platform.system')
    def test_lint_file_with_errors_windows(self, mock_platform, mock_time, mock_run):
        """Test linting a file with syntax errors on Windows."""
        # Setup
        mock_platform.return_value = 'Windows'
        mock_time.side_effect = [0, 2]
        linter = JavaLinter()
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="Test.java:3: error: class, interface, or enum expected"
        )
        
        # Execute
        result = linter.lint_file('Test.java')
        
        # Verify
        assert result.has_issues
        assert "class, interface, or enum expected" in result.lint_output
        assert result.metadata['tools_used'] == ['javac']
        
        # Check the command used (should have javac, -d, temp_dir, --release, 8, -Xlint:all, -proc:none, Test.java)  
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'javac'
        assert call_args[1] == '-d'
        # call_args[2] will be the temporary directory path
        assert call_args[3] == '--release'
        assert call_args[4] == '8'
        assert call_args[5] == '-Xlint:all'
        assert call_args[6] == '-proc:none'
        assert call_args[-1] == 'Test.java'  # File path is last
    
    @patch('subprocess.run')
    def test_lint_file_with_custom_args(self, mock_run):
        """Test linting with custom javac arguments."""
        linter = JavaLinter({
            'javac_args': ['-Xlint:all', '-encoding', 'UTF-8']
        })
        mock_run.return_value = MagicMock(stdout="", stderr="")
        
        linter.lint_file('Test.java')
        
        # Verify javac was called with custom arguments
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'javac'
        assert call_args[1] == '-d'
        # call_args[2] will be the temporary directory path
        assert call_args[3] == '--release'
        assert call_args[4] == '8'
        assert call_args[5] == '-Xlint:all'
        assert call_args[6] == '-proc:none'
        # Custom arguments should appear before the file path
        assert '-Xlint:all' in call_args
        assert '-encoding' in call_args
        assert 'UTF-8' in call_args
        assert call_args[-1] == 'Test.java'  # File path is last
    
    @patch('subprocess.run')
    def test_lint_file_timeout(self, mock_run):
        """Test handling of timeout during linting."""
        linter = JavaLinter()
        mock_run.side_effect = subprocess.TimeoutExpired(['javac'], 30)
        
        result = linter.lint_file('Test.java')
        assert result.success is False
        assert "javac execution timed out" in result.error_message
    
    @patch('subprocess.run')
    def test_lint_file_general_error(self, mock_run):
        """Test handling of general errors during linting."""
        linter = JavaLinter()
        mock_run.side_effect = Exception("Unexpected error")
        
        result = linter.lint_file('Test.java')
        assert result.success is False
        assert "Error running javac: Unexpected error" in result.error_message
    
    @pytest.mark.skipif(not JavaLinter().is_available(), reason="javac not available")
    def test_real_lint_valid_java_file(self, tmp_path):
        """Test linting a real valid Java file."""
        # Create a valid Java file
        java_content = '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''
        java_file = tmp_path / "HelloWorld.java"
        java_file.write_text(java_content)
        
        # Lint the file
        linter = JavaLinter()
        result = linter.lint_file(java_file)
        
        # Verify results
        assert result.success is True
        assert str(java_file) in result.files_checked
        assert not result.has_issues  # No syntax errors
        assert result.lint_output == ""  # No output means no errors
        assert result.metadata['tools_used'] == ['javac']
        assert result.execution_time > 0
    
    @pytest.mark.skipif(not JavaLinter().is_available(), reason="javac not available")
    def test_real_lint_invalid_java_file(self, tmp_path):
        """Test linting a real Java file with syntax errors."""
        # Create a Java file with syntax errors
        java_content = '''
public class TestErrors {
    public static void main(String[] args) {
        // Missing semicolon
        int x = 10
        
        // Undefined variable
        System.out.println(undefinedVar);
        
        // Unclosed string
        String message = "Hello
    }
}
'''
        java_file = tmp_path / "TestErrors.java"
        java_file.write_text(java_content)
        
        # Lint the file
        linter = JavaLinter()
        result = linter.lint_file(java_file)
        
        # Verify results
        assert result.success is True  # Linting succeeded even with syntax errors
        assert str(java_file) in result.files_checked
        assert result.has_issues  # Should have syntax errors
        assert "=== javac ===" in result.lint_output
        assert "error:" in result.lint_output  # javac reports errors
        # Common error patterns we expect
        assert ("';' expected" in result.lint_output or 
                "expected" in result.lint_output)  # Missing semicolon
        assert result.metadata['tools_used'] == ['javac']
        assert result.execution_time > 0
    
    @pytest.mark.skipif(not JavaLinter().is_available(), reason="javac not available")
    def test_real_lint_with_custom_args(self, tmp_path):
        """Test linting with custom javac arguments."""
        # Create a Java file with warnings
        java_content = '''
import java.util.*;  // Wildcard import

public class TestWarnings {
    public static void main(String[] args) {
        List list = new ArrayList();  // Raw type usage
        list.add("test");
    }
}
'''
        java_file = tmp_path / "TestWarnings.java"
        java_file.write_text(java_content)
        
        # Lint with -Xlint:all to show warnings
        linter = JavaLinter({'javac_args': ['-Xlint:all']})
        result = linter.lint_file(java_file)
        
        # Verify results
        assert result.success is True
        assert str(java_file) in result.files_checked
        # With -Xlint:all, we might get warnings about raw types
        # Note: warnings might not always appear in stderr, depends on javac version
        assert result.metadata['tools_used'] == ['javac']
    
    def test_project_type_detection(self, tmp_path):
        """Test automatic project type detection."""
        linter = JavaLinter()
        
        # Test Maven detection
        (tmp_path / "pom.xml").touch()
        assert linter._detect_project_type(tmp_path) == 'maven'
        
        # Test Gradle detection
        (tmp_path / "pom.xml").unlink()
        (tmp_path / "build.gradle").touch()
        assert linter._detect_project_type(tmp_path) == 'gradle'
        
        # Test Gradle Kotlin DSL detection
        (tmp_path / "build.gradle").unlink()
        (tmp_path / "build.gradle.kts").touch()
        assert linter._detect_project_type(tmp_path) == 'gradle'
        
        # Test local project (no build files)
        (tmp_path / "build.gradle.kts").unlink()
        assert linter._detect_project_type(tmp_path) == 'local'
    
    def test_find_project_root(self, tmp_path):
        """Test finding project root directory."""
        linter = JavaLinter()
        
        # Create project structure
        project_root = tmp_path / "myproject"
        src_dir = project_root / "src" / "main" / "java" / "com" / "example"
        src_dir.mkdir(parents=True)
        (project_root / "pom.xml").touch()
        
        java_file = src_dir / "Test.java"
        java_file.touch()
        
        # Test finding project root
        found_root = linter._find_project_root(java_file)
        assert found_root == project_root
    
    def test_find_local_jars(self, tmp_path):
        """Test finding local JAR files."""
        linter = JavaLinter({'lib_dirs': ['lib', 'libs']})
        
        # Create lib directory with JARs
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        (lib_dir / "commons-lang3.jar").touch()
        (lib_dir / "guava.jar").touch()
        
        libs_dir = tmp_path / "libs"
        libs_dir.mkdir()
        (libs_dir / "junit.jar").touch()
        
        # Find JARs
        classpath = linter._find_local_jars(tmp_path)
        assert classpath is not None
        assert "commons-lang3.jar" in classpath
        assert "guava.jar" in classpath
        assert "junit.jar" in classpath
    
    def test_find_source_path(self, tmp_path):
        """Test finding source paths."""
        linter = JavaLinter({'source_paths': ['src', 'src/main/java', 'src/test/java']})
        
        # Create source directories
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main" / "java").mkdir(parents=True)
        
        # Find source paths
        source_path = linter._find_source_path(tmp_path)
        assert source_path is not None
        assert str(tmp_path / "src") in source_path
        assert str(tmp_path / "src" / "main" / "java") in source_path
    
    def test_check_for_module_info(self, tmp_path):
        """Test JPMS module detection."""
        linter = JavaLinter({'source_paths': ['src']})
        
        # Create source directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        # Initially no module-info
        assert linter._check_for_module_info(tmp_path) is False
        
        # Add module-info.java
        (src_dir / "module-info.java").touch()
        assert linter._check_for_module_info(tmp_path) is True
    
    @patch('subprocess.run')
    def test_maven_classpath_resolution(self, mock_run, tmp_path):
        """Test Maven dependency resolution."""
        linter = JavaLinter({'enable_dependency_resolution': True})
        
        # Create pom.xml
        (tmp_path / "pom.xml").touch()
        
        # Mock Maven output
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("/path/to/lib1.jar:/path/to/lib2.jar")
            tmp_file = tmp.name
        
        def side_effect(*args, **kwargs):
            # Write to the output file specified in the command
            cmd = args[0]
            for i, arg in enumerate(cmd):
                if arg.startswith('-Dmdep.outputFile='):
                    output_file = arg.split('=')[1]
                    with open(output_file, 'w') as f:
                        f.write("/path/to/lib1.jar:/path/to/lib2.jar")
            return MagicMock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = side_effect
        
        # Resolve classpath
        classpath = linter._resolve_maven_classpath(tmp_path)
        
        # Verify
        assert classpath is not None
        assert "lib1.jar" in classpath
        assert "lib2.jar" in classpath
        
        # Clean up
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
    
    @patch('subprocess.run')
    def test_gradle_classpath_resolution(self, mock_run, tmp_path):
        """Test Gradle dependency resolution."""
        linter = JavaLinter({'enable_dependency_resolution': True})
        
        # Create build.gradle
        (tmp_path / "build.gradle").touch()
        
        # Mock Gradle output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/path/to/gradle-lib1.jar:/path/to/gradle-lib2.jar",
            stderr=""
        )
        
        # Resolve classpath
        classpath = linter._resolve_gradle_classpath(tmp_path)
        
        # Verify
        assert classpath is not None
        assert "gradle-lib1.jar" in classpath
        assert "gradle-lib2.jar" in classpath
    
    @patch('subprocess.run')
    def test_lint_with_dependencies(self, mock_run, tmp_path):
        """Test linting with resolved dependencies."""
        # Create project structure
        (tmp_path / "pom.xml").touch()
        src_dir = tmp_path / "src" / "main" / "java"
        src_dir.mkdir(parents=True)
        
        java_file = src_dir / "Test.java"
        java_file.write_text("""
import org.apache.commons.lang3.StringUtils;

public class Test {
    public static void main(String[] args) {
        String result = StringUtils.capitalize("hello");
    }
}
""")
        
        # Configure linter
        linter = JavaLinter({
            'enable_dependency_resolution': True,
            'source_paths': ['src/main/java']
        })
        
        # Mock Maven to return commons-lang3 in classpath
        def maven_side_effect(*args, **kwargs):
            cmd = args[0]
            if 'dependency:build-classpath' in cmd:
                for arg in cmd:
                    if arg.startswith('-Dmdep.outputFile='):
                        output_file = arg.split('=')[1]
                        with open(output_file, 'w') as f:
                            f.write("/path/to/commons-lang3.jar")
                return MagicMock(returncode=0)
            # For javac call
            return MagicMock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = maven_side_effect
        
        # Lint the file
        result = linter.lint_file(java_file)
        
        # Verify
        assert result.success is True
        assert result.metadata.get('classpath_resolved') is True
        assert result.metadata.get('project_type') == 'maven'
        
        # Check that javac was called with classpath
        javac_calls = [call for call in mock_run.call_args_list if 'javac' in str(call)]
        assert len(javac_calls) > 0
        javac_args = javac_calls[0][0][0]
        assert '-classpath' in javac_args or '--module-path' in javac_args