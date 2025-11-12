"""
Error recovery module for shell command execution.

This module provides error recovery functionality including:
- Error handling strategies
- Automatic recovery mechanisms
- Retry logic with backoff
- Error categorization and logging
"""

import time
import random
from typing import Dict, Type, Callable, Optional, Any, List, Union
from loguru import logger

from .exceptions import (
    CommandExecutionError,
    CommandTimeoutError,
    ProcessCleanupError,
    ProcessNotFoundError,
    ErrorRecoveryFailedError
)


class ErrorRecoveryManager:
    """
    Manager for error recovery and handling.
    
    This class provides comprehensive error recovery mechanisms including
    retry logic, error categorization, and custom recovery strategies.
    
    Attributes:
        recovery_strategies: Dictionary mapping exception types to recovery functions
        retry_config: Configuration for retry behavior
        max_recovery_attempts: Maximum number of recovery attempts
    """
    
    def __init__(self, max_recovery_attempts: int = 3):
        """
        Initialize error recovery manager.
        
        Args:
            max_recovery_attempts: Maximum number of recovery attempts
        """
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_strategies: Dict[Type[Exception], Callable] = {
            CommandTimeoutError: self._handle_timeout_error,
            ProcessCleanupError: self._handle_cleanup_error,
            ProcessNotFoundError: self._handle_process_not_found_error,
            CommandExecutionError: self._handle_execution_error,
        }
        
        logger.debug(f"ErrorRecoveryManager initialized with max_attempts={max_recovery_attempts}")
    
    def register_recovery_strategy(
        self,
        exception_type: Type[Exception],
        strategy: Callable
    ) -> None:
        """
        Register a custom recovery strategy for an exception type.
        
        Args:
            exception_type: The exception type to handle
            strategy: The recovery function to use
        """
        self.recovery_strategies[exception_type] = strategy
        logger.debug(f"Registered recovery strategy for {exception_type.__name__}")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> bool:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error: The exception to handle
            context: Additional context information
            retry_count: Current retry attempt number
            
        Returns:
            True if recovery was successful, False otherwise
            
        Raises:
            ErrorRecoveryFailedError: If all recovery attempts fail
        """
        if context is None:
            context = {}
        
        error_type = type(error)
        
        logger.warning(f"Handling error: {error_type.__name__}: {error}")
        
        # Check if we have a recovery strategy for this error type
        strategy = self._get_recovery_strategy(error_type)
        if not strategy:
            logger.error(f"No recovery strategy found for {error_type.__name__}")
            return False
        
        # Attempt recovery
        try:
            success = strategy(error, context, retry_count)
            
            if success:
                logger.info(f"Successfully recovered from {error_type.__name__}")
                return True
            else:
                logger.warning(f"Recovery failed for {error_type.__name__}")
                
                # Check if we should retry
                if retry_count < self.max_recovery_attempts:
                    logger.debug(f"Retrying recovery, attempt {retry_count + 1}/{self.max_recovery_attempts}")
                    return self.handle_error(error, context, retry_count + 1)
                else:
                    logger.error(f"Max recovery attempts reached for {error_type.__name__}")
                    raise ErrorRecoveryFailedError(error, retry_count)
                    
        except Exception as e:
            logger.error(f"Error during recovery attempt: {e}")
            if retry_count < self.max_recovery_attempts:
                return self.handle_error(error, context, retry_count + 1)
            else:
                raise ErrorRecoveryFailedError(error, retry_count)
    
    def _get_recovery_strategy(self, error_type: Type[Exception]) -> Optional[Callable]:
        """
        Get the appropriate recovery strategy for an error type.
        
        Args:
            error_type: The exception type
            
        Returns:
            Recovery strategy function or None
        """
        # Check for exact match first
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type]
        
        # Check for parent class matches
        for exception_type, strategy in self.recovery_strategies.items():
            if issubclass(error_type, exception_type):
                return strategy
        
        return None
    
    def _handle_timeout_error(
        self,
        error: CommandTimeoutError,
        context: Dict[str, Any],
        retry_count: int
    ) -> bool:
        """
        Handle command timeout errors.
        
        Args:
            error: The timeout error
            context: Context information
            retry_count: Current retry attempt
            
        Returns:
            True if recovery successful
        """
        logger.debug(f"Handling timeout error for command: {error.command}")
        
        # Strategy 1: Increase timeout and retry
        if retry_count == 0:
            new_timeout = error.timeout * 1.5
            logger.debug(f"Increasing timeout to {new_timeout}s and retrying")
            context['timeout'] = new_timeout
            return True
        
        # Strategy 2: Try with even longer timeout
        elif retry_count == 1:
            new_timeout = error.timeout * 2.0
            logger.debug(f"Increasing timeout to {new_timeout}s (final attempt)")
            context['timeout'] = new_timeout
            return True
        
        # Strategy 3: Give up
        else:
            logger.error(f"Unable to recover from timeout error after {retry_count} attempts")
            return False
    
    def _handle_cleanup_error(
        self,
        error: ProcessCleanupError,
        context: Dict[str, Any],
        retry_count: int
    ) -> bool:
        """
        Handle process cleanup errors.
        
        Args:
            error: The cleanup error
            context: Context information
            retry_count: Current retry attempt
            
        Returns:
            True if recovery successful
        """
        logger.debug(f"Handling cleanup error for PID: {error.pid}")
        
        # Strategy 1: Wait and retry cleanup
        if retry_count == 0:
            logger.debug("Waiting before retry cleanup")
            time.sleep(1.0)
            return True
        
        # Strategy 2: Force cleanup with longer timeout
        elif retry_count == 1:
            logger.debug("Attempting force cleanup with longer timeout")
            context['force_cleanup'] = True
            context['cleanup_timeout'] = 15.0
            return True
        
        # Strategy 3: Log and continue (non-fatal)
        else:
            logger.warning(f"Unable to cleanup process {error.pid}, continuing anyway")
            return True  # Consider cleanup errors non-fatal
    
    def _handle_process_not_found_error(
        self,
        error: ProcessNotFoundError,
        context: Dict[str, Any],
        retry_count: int
    ) -> bool:
        """
        Handle process not found errors.
        
        Args:
            error: The process not found error
            context: Context information
            retry_count: Current retry attempt
            
        Returns:
            True if recovery successful
        """
        logger.debug(f"Handling process not found error for PID: {error.pid}")
        
        # Process not found is usually not a real error - process already exited
        logger.debug(f"Process {error.pid} not found, likely already exited")
        return True
    
    def _handle_execution_error(
        self,
        error: CommandExecutionError,
        context: Dict[str, Any],
        retry_count: int
    ) -> bool:
        """
        Handle general command execution errors.
        
        Args:
            error: The execution error
            context: Context information
            retry_count: Current retry attempt
            
        Returns:
            True if recovery successful
        """
        logger.debug(f"Handling execution error: {error}")
        
        # Strategy 1: Simple retry
        if retry_count == 0:
            logger.debug("Retrying command execution")
            return True
        
        # Strategy 2: Wait and retry
        elif retry_count == 1:
            logger.debug("Waiting before retry")
            time.sleep(0.5)
            return True
        
        # Strategy 3: Give up
        else:
            logger.error(f"Unable to recover from execution error after {retry_count} attempts")
            return False

    def _validate_delays(self, delays: List[float]) -> List[float]:
        """
        Validate retry delays.
        
        Args:
            delays: List of delays to validate
            
        Returns:
            Validated delays
            
        Raises:
            ValueError: If delays are invalid
        """
        if not delays:
            raise ValueError("Delays cannot be empty")
        
        # Fix negative delays by setting them to 0
        validated_delays = []
        for delay in delays:
            if delay < 0:
                validated_delays.append(0.0)  # Set negative delays to 0
            else:
                validated_delays.append(delay)
        
        return validated_delays


class RetryConfig:
    """
    Configuration for retry behavior.
    
    Attributes:
        max_retries: Maximum number of retries (0 means no retries)
        delays: Custom delay sequence (if None, uses exponential backoff)
        backoff_factor: Factor for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on_timeout: Whether to retry on timeout
        retry_on_error: Whether to retry on other errors
    """
    
    def __init__(
        self,
        max_retries: Optional[int] = None,
        delays: Optional[List[float]] = None,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_timeout: bool = True,
        retry_on_error: bool = True,
        # Backward compatibility parameters
        max_attempts: Optional[int] = None,
        base_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        retry_on_cleanup_error: Optional[bool] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retries (0 means no retries)
            delays: Custom delay sequence (if None, uses exponential backoff)
            backoff_factor: Factor for exponential backoff
            jitter: Whether to add random jitter to delays
            retry_on_timeout: Whether to retry on timeout
            retry_on_error: Whether to retry on other errors
            
            # Backward compatibility:
            max_attempts: Old name for max_retries
            base_delay: Base delay for old exponential backoff
            max_delay: Maximum delay for old exponential backoff
            retry_on_cleanup_error: Old name for retry_on_error
        """
        # Handle backward compatibility
        if max_attempts is not None:
            max_retries = max_attempts
        if max_retries is None:
            max_retries = 3
            
        if retry_on_cleanup_error is not None:
            retry_on_error = retry_on_cleanup_error
            
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        self.max_retries = max_retries
        # For backward compatibility
        self.max_attempts = max_retries
        
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_error = retry_on_error
        self.retry_on_cleanup_error = retry_on_error  # Backward compatibility
        
        # Handle old-style delay configuration
        if base_delay is not None or max_delay is not None:
            # Use old exponential backoff style
            self.base_delay = base_delay if base_delay is not None else 1.0
            self.max_delay = max_delay if max_delay is not None else 60.0
            
            if max_retries == 0:
                self.delays = []
            else:
                # Generate delays using old style
                self.delays = []
                for i in range(max_retries):
                    delay = self.base_delay * (backoff_factor ** i)
                    delay = min(delay, self.max_delay)
                    # Fix negative delays
                    delay = max(0.0, delay)
                    self.delays.append(delay)
        else:
            # Use new style delay configuration
            self.base_delay = 1.0  # Default for backward compatibility
            self.max_delay = 60.0  # Default for backward compatibility
            
            if delays is not None:
                # Validate and fix delays directly
                if not delays:
                    raise ValueError("Delays cannot be empty")
                
                # Fix negative delays by setting them to 0
                validated_delays = []
                for delay in delays:
                    if delay < 0:
                        validated_delays.append(0.0)  # Set negative delays to 0
                    else:
                        validated_delays.append(delay)
                
                self.delays = validated_delays
            else:
                # Generate default delays based on max_retries
                if max_retries == 0:
                    self.delays = []  # No retries, no delays needed
                else:
                    self.delays = [min(60.0, backoff_factor ** i) for i in range(max_retries)]
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay for a specific retry attempt.
        
        Args:
            attempt: The retry attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Ensure attempt is within bounds, use last delay for out-of-bounds
        if attempt < 0:
            attempt = 0
        elif attempt >= len(self.delays):
            attempt = len(self.delays) - 1 if self.delays else 0
            
        # If no delays configured, return 0
        if not self.delays:
            return 0.0
            
        delay = self.delays[attempt]
        if self.jitter:
            delay += random.uniform(-0.1 * delay, 0.1 * delay)
        # Ensure delay is never negative
        return max(0.0, delay)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            attempt: The current attempt number
            
        Returns:
            True if should retry
        """
        if attempt >= self.max_attempts:
            return False
        
        if isinstance(error, CommandTimeoutError):
            return self.retry_on_timeout
        
        if isinstance(error, ProcessCleanupError):
            return self.retry_on_error
        
        if isinstance(error, ProcessNotFoundError):
            return False  # Don't retry process not found errors
        
        if isinstance(error, CommandExecutionError):
            return self.retry_on_error  # Retry general execution errors
        
        return False


def retry_with_backoff(
    func: Callable,
    retry_config: RetryConfig,
    error_recovery_manager: Optional[ErrorRecoveryManager] = None,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        retry_config: Retry configuration
        error_recovery_manager: Optional error recovery manager
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    
    # Use max_attempts directly from config (which handles backward compatibility)
    max_attempts = max(1, retry_config.max_attempts)
    
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # If this is the last attempt or we shouldn't retry, break
            if attempt >= max_attempts or not retry_config.should_retry(e, attempt):
                logger.debug(f"Not retrying {type(e).__name__} on attempt {attempt}")
                break
            
            # Try error recovery if available
            if error_recovery_manager:
                try:
                    if error_recovery_manager.handle_error(e, retry_count=attempt):
                        logger.debug(f"Error recovery successful for attempt {attempt}")
                        continue
                except ErrorRecoveryFailedError:
                    logger.debug(f"Error recovery failed for attempt {attempt}")
                    break
            
            # Calculate delay
            delay = retry_config.get_delay(attempt)
            logger.debug(f"Retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)
    
    # All retries failed
    if last_exception:
        raise last_exception
    else:
        raise CommandExecutionError("All retry attempts failed")


def create_default_error_recovery_manager() -> ErrorRecoveryManager:
    """
    Create a default error recovery manager with standard strategies.
    
    Returns:
        Configured ErrorRecoveryManager instance
    """
    return ErrorRecoveryManager(max_recovery_attempts=3) 