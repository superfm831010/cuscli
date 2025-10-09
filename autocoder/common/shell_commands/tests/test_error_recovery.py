"""
Tests for error recovery functionality.

This module tests the error recovery mechanisms used in shell command execution.
"""

import pytest
import time
from unittest.mock import Mock, patch

from autocoder.common.shell_commands.error_recovery import (
    ErrorRecoveryManager,
    RetryConfig,
    create_default_error_recovery_manager,
    retry_with_backoff
)
from autocoder.common.shell_commands.exceptions import (
    CommandExecutionError,
    CommandTimeoutError,
    ErrorRecoveryFailedError
)


class TestRetryConfig:
    """Test cases for RetryConfig class."""
    
    def test_initialization_defaults(self):
        """Test RetryConfig initialization with default values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.retry_on_timeout is True
        assert config.retry_on_cleanup_error is True
    
    def test_initialization_custom(self):
        """Test RetryConfig initialization with custom values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            backoff_factor=3.0,
            retry_on_timeout=False,
            retry_on_cleanup_error=False
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_factor == 3.0
        assert config.retry_on_timeout is False
        assert config.retry_on_cleanup_error is False
    
    def test_get_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=10.0, jitter=False)
        
        assert config.get_delay(0) == 1.0  # base_delay * 2^0
        assert config.get_delay(1) == 2.0  # base_delay * 2^1
        assert config.get_delay(2) == 4.0  # base_delay * 2^2
    
    def test_get_delay_max_limit(self):
        """Test that delay calculation respects maximum limit."""
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=5.0, jitter=False)
        
        # Even with exponential backoff, delay should not exceed max_delay
        delay_high = config.get_delay(10)  # Very high attempt number
        assert delay_high <= 5.0
    
    def test_should_retry_timeout_error(self):
        """Test retry decision for timeout errors."""
        config = RetryConfig(retry_on_timeout=True)
        timeout_error = CommandTimeoutError("test", 5.0, 123)
        assert config.should_retry(timeout_error, 0)
        assert config.should_retry(timeout_error, 1)
        assert config.should_retry(timeout_error, 2)
        assert not config.should_retry(timeout_error, 3)  # Max attempts reached
    
    def test_should_retry_timeout_disabled(self):
        """Test retry decision when timeout retry is disabled."""
        config = RetryConfig(retry_on_timeout=False)
        timeout_error = CommandTimeoutError("test", 5.0, 123)
        assert not config.should_retry(timeout_error, 0)
    
    def test_should_retry_generic_error(self):
        """Test retry decision for generic errors."""
        config = RetryConfig()
        generic_error = Exception("Generic error")
        assert not config.should_retry(generic_error, 0)


class TestErrorRecoveryManager:
    """Test cases for ErrorRecoveryManager class."""
    
    def test_initialization_defaults(self):
        """Test manager initialization with default values."""
        manager = ErrorRecoveryManager()
        assert manager.max_recovery_attempts == 3
        assert len(manager.recovery_strategies) > 0
    
    def test_initialization_custom(self):
        """Test manager initialization with custom values."""
        manager = ErrorRecoveryManager(max_recovery_attempts=5)
        assert manager.max_recovery_attempts == 5
    
    def test_register_recovery_strategy(self):
        """Test registering custom recovery strategies."""
        manager = ErrorRecoveryManager()
        
        def custom_strategy(error, context, retry_count):
            return True
        
        manager.register_recovery_strategy(ValueError, custom_strategy)
        assert ValueError in manager.recovery_strategies
    
    def test_handle_error_success(self):
        """Test successful error recovery."""
        manager = ErrorRecoveryManager()
        
        # Mock a successful recovery
        def mock_strategy(error, context, retry_count):
            return True
        
        manager.register_recovery_strategy(ValueError, mock_strategy)
        
        error = ValueError("Test error")
        result = manager.handle_error(error)
        assert result is True
    
    def test_handle_error_failure(self):
        """Test failed error recovery."""
        manager = ErrorRecoveryManager(max_recovery_attempts=1)
        
        # Mock a failed recovery
        def mock_strategy(error, context, retry_count):
            return False
        
        manager.register_recovery_strategy(ValueError, mock_strategy)
        
        error = ValueError("Test error")
        with pytest.raises(ErrorRecoveryFailedError):
            manager.handle_error(error)
    
    def test_handle_error_no_strategy(self):
        """Test error handling when no strategy is available."""
        manager = ErrorRecoveryManager()
        
        # Use an error type that doesn't have a strategy
        error = KeyError("Test error")
        result = manager.handle_error(error)
        assert result is False


class TestRetryWithBackoff:
    """Test cases for retry_with_backoff function."""
    
    def test_retry_success_on_first_try(self):
        """Test successful execution on first try."""
        call_count = 0
        
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        config = RetryConfig()
        result = retry_with_backoff(successful_func, config)
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test successful execution after initial failures."""
        call_count = 0
        
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CommandTimeoutError("test", 5.0, 123)
            return "success"
        
        config = RetryConfig(max_attempts=5, retry_on_timeout=True)
        result = retry_with_backoff(flaky_func, config)
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test behavior when max attempts is exceeded."""
        call_count = 0
        
        def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise CommandTimeoutError("test", 5.0, 123)
        
        config = RetryConfig(max_attempts=2, retry_on_timeout=True)
        with pytest.raises(CommandTimeoutError):
            retry_with_backoff(always_fail_func, config)
        
        assert call_count == 2
    
    def test_retry_non_retryable_error(self):
        """Test behavior with non-retryable errors."""
        call_count = 0
        
        def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        config = RetryConfig()
        with pytest.raises(ValueError):
            retry_with_backoff(non_retryable_func, config)
        
        assert call_count == 1
    
    @patch('time.sleep')
    def test_retry_delay_timing(self, mock_sleep):
        """Test that delays are applied correctly."""
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CommandTimeoutError("test", 5.0, 123)
            return "success"
        
        config = RetryConfig(base_delay=1.0, max_attempts=3, retry_on_timeout=True, jitter=False)
        result = retry_with_backoff(failing_func, config)
        
        assert result == "success"
        assert mock_sleep.call_count == 2  # Two retries, two delays
        
        # Check that delays follow expected pattern
        expected_delays = [1.0, 2.0]  # Exponential backoff
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays


class TestDefaultErrorRecoveryManager:
    """Test cases for default error recovery manager."""
    
    def test_create_default_manager(self):
        """Test creating default error recovery manager."""
        manager = create_default_error_recovery_manager()
        assert isinstance(manager, ErrorRecoveryManager)
        assert manager.max_recovery_attempts == 3
        assert len(manager.recovery_strategies) > 0
    
    def test_default_timeout_error_handling(self):
        """Test default handling of timeout errors."""
        manager = create_default_error_recovery_manager()
        
        timeout_error = CommandTimeoutError("test", 5.0, 123)
        context = {}
        
        # Should attempt recovery
        result = manager.handle_error(timeout_error, context)
        assert result is True  # Should succeed on first try with increased timeout
        assert 'timeout' in context  # Context should be updated with new timeout


class TestErrorRecoveryEdgeCases:
    """Test cases for edge cases and error conditions."""
    
    def test_zero_max_attempts(self):
        """Test behavior with zero max attempts."""
        config = RetryConfig(max_attempts=0)
        
        def failing_func():
            raise CommandTimeoutError("test", 5.0, 123)
        
        with pytest.raises(CommandTimeoutError):
            retry_with_backoff(failing_func, config)
    
    def test_negative_delay_values(self):
        """Test behavior with negative delay values."""
        config = RetryConfig(base_delay=-1.0)
        
        # Should handle negative delays gracefully
        delay = config.get_delay(1)
        assert delay >= 0  # Should not return negative delays
    
    def test_function_with_side_effects(self):
        """Test retry behavior with functions that have side effects."""
        side_effects = []
        
        def side_effect_func():
            side_effects.append("called")
            if len(side_effects) < 2:
                raise CommandTimeoutError("test", 5.0, 123)
            return "success"
        
        config = RetryConfig(max_attempts=3, retry_on_timeout=True)
        result = retry_with_backoff(side_effect_func, config)
        
        assert result == "success"
        assert len(side_effects) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 