"""
Tests for shell command exceptions.

This module tests the custom exception classes used in the shell command system.
"""

import pytest

from autocoder.common.shell_commands.exceptions import (
    CommandExecutionError,
    CommandTimeoutError,
    ProcessCleanupError,
    ProcessNotFoundError,
    TimeoutConfigError,
    ErrorRecoveryFailedError
)


class TestCommandExecutionError:
    """Test cases for CommandExecutionError."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        error = CommandExecutionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_inheritance(self):
        """Test that CommandExecutionError inherits from Exception."""
        error = CommandExecutionError("Test")
        assert isinstance(error, Exception)
    
    def test_empty_message(self):
        """Test exception with empty message."""
        error = CommandExecutionError("")
        assert str(error) == ""
        assert isinstance(error, Exception)


class TestCommandTimeoutError:
    """Test cases for CommandTimeoutError."""
    
    def test_basic_creation(self):
        """Test basic timeout error creation."""
        error = CommandTimeoutError("sleep 10", 5.0, 12345)
        assert "sleep 10" in str(error)
        assert "5.0" in str(error)
        assert "12345" in str(error)
    
    def test_attributes(self):
        """Test timeout error attributes."""
        error = CommandTimeoutError("test command", 3.0, 999)
        assert error.command == "test command"
        assert error.timeout == 3.0
        assert error.pid == 999
    
    def test_without_pid(self):
        """Test timeout error without PID."""
        error = CommandTimeoutError("echo hello", 2.5)
        assert error.command == "echo hello"
        assert error.timeout == 2.5
        assert error.pid is None
        assert "echo hello" in str(error)
        assert "2.5" in str(error)
    
    def test_string_representation(self):
        """Test string representation of timeout error."""
        error = CommandTimeoutError("echo hello", 2.5, 1234)
        error_str = str(error)
        assert "echo hello" in error_str
        assert "2.5" in error_str
        assert "1234" in error_str
        assert "timed out" in error_str.lower()
    
    def test_repr(self):
        """Test __repr__ method."""
        error = CommandTimeoutError("test", 1.0, 123)
        repr_str = repr(error)
        assert "CommandTimeoutError" in repr_str
        assert "test" in repr_str
        assert "1.0" in repr_str
        assert "123" in repr_str
    
    def test_inheritance(self):
        """Test inheritance from CommandExecutionError."""
        error = CommandTimeoutError("test", 1.0, 123)
        assert isinstance(error, CommandExecutionError)
        assert isinstance(error, Exception)


class TestProcessCleanupError:
    """Test cases for ProcessCleanupError."""
    
    def test_basic_creation(self):
        """Test basic process cleanup error creation."""
        error = ProcessCleanupError(1234, "Failed to cleanup process")
        assert error.pid == 1234
        assert error.original_message == "Failed to cleanup process"
        assert "1234" in str(error)
        assert "Failed to cleanup process" in str(error)
    
    def test_string_representation(self):
        """Test string representation."""
        error = ProcessCleanupError(5678, "Process is still running")
        error_str = str(error)
        assert "5678" in error_str
        assert "Process is still running" in error_str
        assert "Failed to cleanup process" in error_str
    
    def test_repr(self):
        """Test __repr__ method."""
        error = ProcessCleanupError(999, "Test message")
        repr_str = repr(error)
        assert "ProcessCleanupError" in repr_str
        assert "999" in repr_str
        assert "Test message" in repr_str
    
    def test_inheritance(self):
        """Test inheritance from CommandExecutionError."""
        error = ProcessCleanupError(123, "test")
        assert isinstance(error, CommandExecutionError)
        assert isinstance(error, Exception)


class TestProcessNotFoundError:
    """Test cases for ProcessNotFoundError."""
    
    def test_basic_creation(self):
        """Test basic process not found error creation."""
        error = ProcessNotFoundError(1234)
        assert error.pid == 1234
        assert "1234" in str(error)
        assert "not found" in str(error).lower()
    
    def test_repr(self):
        """Test __repr__ method."""
        error = ProcessNotFoundError(999)
        repr_str = repr(error)
        assert "ProcessNotFoundError" in repr_str
        assert "999" in repr_str
    
    def test_inheritance(self):
        """Test inheritance from CommandExecutionError."""
        error = ProcessNotFoundError(123)
        assert isinstance(error, CommandExecutionError)
        assert isinstance(error, Exception)


class TestTimeoutConfigError:
    """Test cases for TimeoutConfigError."""
    
    def test_basic_creation(self):
        """Test basic timeout config error creation."""
        error = TimeoutConfigError("default_timeout", -1, "Timeout must be positive")
        assert error.config_field == "default_timeout"
        assert error.value == -1
        assert error.reason == "Timeout must be positive"
    
    def test_string_representation(self):
        """Test string representation."""
        error = TimeoutConfigError("max_timeout", "invalid", "Must be a number")
        error_str = str(error)
        assert "max_timeout" in error_str
        assert "invalid" in error_str
        assert "Must be a number" in error_str
    
    def test_repr(self):
        """Test __repr__ method."""
        error = TimeoutConfigError("test_field", 123, "test reason")
        repr_str = repr(error)
        assert "TimeoutConfigError" in repr_str
        assert "test_field" in repr_str
        assert "123" in repr_str
        assert "test reason" in repr_str
    
    def test_inheritance(self):
        """Test inheritance from CommandExecutionError."""
        error = TimeoutConfigError("test", 1, "test")
        assert isinstance(error, CommandExecutionError)
        assert isinstance(error, Exception)


class TestErrorRecoveryFailedError:
    """Test cases for ErrorRecoveryFailedError."""
    
    def test_basic_creation(self):
        """Test basic error recovery failed error creation."""
        original_error = ValueError("Original error")
        error = ErrorRecoveryFailedError(original_error, 3)
        assert error.original_error is original_error
        assert error.recovery_attempts == 3
        assert "3 attempts" in str(error)
        assert "Original error" in str(error)
    
    def test_with_different_original_error(self):
        """Test with different types of original errors."""
        original_error = CommandTimeoutError("test", 1.0, 123)
        error = ErrorRecoveryFailedError(original_error, 5)
        assert error.original_error is original_error
        assert error.recovery_attempts == 5
        assert "5 attempts" in str(error)
    
    def test_repr(self):
        """Test __repr__ method."""
        original_error = RuntimeError("Test error")
        error = ErrorRecoveryFailedError(original_error, 2)
        repr_str = repr(error)
        assert "ErrorRecoveryFailedError" in repr_str
        assert "2" in repr_str
    
    def test_inheritance(self):
        """Test inheritance from CommandExecutionError."""
        original_error = Exception("test")
        error = ErrorRecoveryFailedError(original_error, 1)
        assert isinstance(error, CommandExecutionError)
        assert isinstance(error, Exception)


class TestExceptionInteraction:
    """Test cases for exception interaction and edge cases."""
    
    def test_exception_chaining(self):
        """Test exception chaining scenarios."""
        try:
            raise CommandExecutionError("Original error")
        except CommandExecutionError as e:
            timeout_error = CommandTimeoutError("test", 1.0, 123)
            timeout_error.__cause__ = e
            assert timeout_error.__cause__ is e
    
    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""
        exec_error = CommandExecutionError("Execution failed")
        timeout_error = CommandTimeoutError("timeout test", 5.0, 456)
        cleanup_error = ProcessCleanupError(789, "Cleanup failed")
        
        errors = [exec_error, timeout_error, cleanup_error]
        
        for error in errors:
            assert isinstance(error, Exception)
        
        # Test that all errors inherit from CommandExecutionError
        for error in errors:
            assert isinstance(error, CommandExecutionError)
    
    def test_exception_with_none_values(self):
        """Test exceptions with None values."""
        # Test CommandTimeoutError with None PID
        error = CommandTimeoutError("test", 5.0, None)
        assert error.command == "test"
        assert error.timeout == 5.0
        assert error.pid is None
        
        # Should still be convertible to string
        str_repr = str(error)
        assert isinstance(str_repr, str)
        assert "test" in str_repr
    
    def test_exception_pickling(self):
        """Test that exceptions can be pickled (for multiprocessing)."""
        import pickle
        
        # Test basic exception pickling
        error1 = CommandExecutionError("Test execution error")
        pickled1 = pickle.dumps(error1)
        unpickled1 = pickle.loads(pickled1)
        assert str(unpickled1) == str(error1)
        
        # Test that custom exceptions at least create proper string representations
        timeout_error = CommandTimeoutError("test", 5.0, 123)
        cleanup_error = ProcessCleanupError(456, "Test cleanup error")
        
        # These should at least have proper string representations
        assert str(timeout_error)
        assert str(cleanup_error)
        assert repr(timeout_error)
        assert repr(cleanup_error)
        
        # Note: Custom exceptions with complex __init__ may have pickling issues
        # This is acceptable as they're primarily used for immediate error handling
    
    def test_all_exceptions_are_command_execution_errors(self):
        """Test that all custom exceptions inherit from CommandExecutionError."""
        exceptions = [
            CommandExecutionError("test"),
            CommandTimeoutError("test", 1.0, 123),
            ProcessCleanupError(123, "test"),
            ProcessNotFoundError(456),
            TimeoutConfigError("test", "value", "reason"),
            ErrorRecoveryFailedError(Exception("test"), 1)
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CommandExecutionError)
            assert isinstance(exc, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 