"""
Custom exceptions for shell command execution with timeout support.

This module defines all custom exceptions used in the shell commands module
for proper error handling and recovery.
"""

from typing import Optional, Any


class CommandExecutionError(Exception):
    """
    Base exception for command execution errors.
    
    This is the base class for all command execution related exceptions.
    """
    pass


class CommandTimeoutError(CommandExecutionError):
    """
    Exception raised when a command execution times out.
    
    Attributes:
        command: The command that timed out
        timeout: The timeout value in seconds
        pid: The process ID that timed out (if available)
    """
    
    def __init__(self, command: str, timeout: float, pid: Optional[int] = None):
        self.command = command
        self.timeout = timeout
        self.pid = pid
        
        message = f"Command '{command}' timed out after {timeout} seconds"
        if pid:
            message += f" (PID: {pid})"
            
        super().__init__(message)
    
    def __str__(self) -> str:
        return super().__str__()
    
    def __repr__(self) -> str:
        return f"CommandTimeoutError(command={self.command!r}, timeout={self.timeout}, pid={self.pid})"


class ProcessCleanupError(CommandExecutionError):
    """
    Exception raised when process cleanup fails.
    
    Attributes:
        pid: The process ID that failed to cleanup
        message: Detailed error message
    """
    
    def __init__(self, pid: int, message: str):
        self.pid = pid
        self.original_message = message
        super().__init__(f"Failed to cleanup process {pid}: {message}")
    
    def __repr__(self) -> str:
        return f"ProcessCleanupError(pid={self.pid}, message={self.original_message!r})"


class ProcessNotFoundError(CommandExecutionError):
    """
    Exception raised when a process is not found during cleanup or management.
    
    Attributes:
        pid: The process ID that was not found
    """
    
    def __init__(self, pid: int):
        self.pid = pid
        super().__init__(f"Process {pid} not found")
    
    def __repr__(self) -> str:
        return f"ProcessNotFoundError(pid={self.pid})"


class TimeoutConfigError(CommandExecutionError):
    """
    Exception raised when there's an error in timeout configuration.
    
    Attributes:
        config_field: The configuration field that caused the error
        value: The invalid value
        reason: The reason why the value is invalid
    """
    
    def __init__(self, config_field: str, value: Any, reason: str):
        self.config_field = config_field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid timeout configuration for '{config_field}': {reason} (value: {value})")
    
    def __repr__(self) -> str:
        return f"TimeoutConfigError(config_field={self.config_field!r}, value={self.value!r}, reason={self.reason!r})"


class ErrorRecoveryFailedError(CommandExecutionError):
    """
    Exception raised when error recovery mechanisms fail.
    
    Attributes:
        original_error: The original error that triggered recovery
        recovery_attempts: Number of recovery attempts made
    """
    
    def __init__(self, original_error: Exception, recovery_attempts: int):
        self.original_error = original_error
        self.recovery_attempts = recovery_attempts
        super().__init__(
            f"Error recovery failed after {recovery_attempts} attempts. "
            f"Original error: {original_error}"
        )
    
    def __repr__(self) -> str:
        return f"ErrorRecoveryFailedError(original_error={self.original_error!r}, recovery_attempts={self.recovery_attempts})" 