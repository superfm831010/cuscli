"""
Shell Commands Module

This module provides comprehensive shell command execution capabilities
including timeout control, process management, error recovery, and 
interactive session management with process type switching support.

Main Components:
- CommandExecutor: Main command execution interface
- TimeoutConfig, TimeoutManager: Timeout control system  
- ProcessManager: Process lifecycle management
- InteractiveCommandExecutor: Interactive command execution
- InteractiveProcess: Standard subprocess-based interactive process
- InteractivePexpectProcess: pexpect-based interactive process
- InteractiveSessionManager: Session management with process type switching
- Error recovery and process cleanup utilities

Usage:
    # Basic command execution
    from autocoder.common.shell_commands import CommandExecutor
    executor = CommandExecutor()
    result = executor.execute_command("ls -la")
    
    # Interactive sessions with process type control
    from autocoder.common.shell_commands import get_session_manager
    manager = get_session_manager()
    
    # Auto-select process type
    result = manager.create_session("python3")
    
    # Explicit process type selection
    result = manager.create_session("python3", use_pexpect=True)
    result = manager.create_session("echo test", use_pexpect=False)
"""

# Core command execution
from .command_executor import (
    CommandExecutor,
    execute_command,
    execute_command_generator,
    execute_command_background,
    execute_commands,
    get_background_processes,
    get_background_process_info,
    cleanup_background_process
)
from .exceptions import (
    CommandExecutionError,
    CommandTimeoutError,
    ProcessCleanupError
)

# Timeout management
from .timeout_config import TimeoutConfig
from .timeout_manager import TimeoutManager

# Process management
from .process_manager import ProcessManager
from .process_cleanup import cleanup_process_tree

# Interactive execution
from .interactive_executor import (
    InteractiveCommandExecutor, 
    InteractiveSession,
    execute_interactive,
    create_interactive_shell
)
from .interactive_process import InteractiveProcess

# pexpect-based execution
from .interactive_pexpect_process import (
    InteractivePexpectProcess, 
    PEXPECT_AVAILABLE
)

# Enhanced session management
from .interactive_session_manager import (
    InteractiveSessionManager,
    EnhancedSessionHandle,
    ProcessType,
    ToolResult,
    get_session_manager,
    clean_terminal_output
)

# Error recovery
from .error_recovery import ErrorRecoveryManager

# Monitoring
from .monitoring import CommandExecutionLogger, PerformanceMonitor
from .background_process_notifier import (
    BackgroundProcessNotifier,
    get_background_process_notifier,
    AsyncTaskMessage,
)

# Version information
__version__ = "1.2.0"

# Convenience exports
__all__ = [
    # Core execution
    "CommandExecutor",
    "execute_command",
    "execute_command_generator", 
    "execute_command_background",
    "execute_commands",
    "get_background_processes",
    "get_background_process_info",
    "cleanup_background_process",
    
    # Exceptions
    "CommandExecutionError",
    "CommandTimeoutError", 
    "ProcessCleanupError",
    
    # Timeout management
    "TimeoutConfig",
    "TimeoutManager",
    
    # Process management
    "ProcessManager",
    "cleanup_process_tree",
    
    # Interactive execution
    "InteractiveCommandExecutor",
    "InteractiveSession",
    "InteractiveProcess",
    "execute_interactive",
    "create_interactive_shell",
    
    # pexpect support
    "InteractivePexpectProcess",
    "PEXPECT_AVAILABLE",
    
    # Enhanced session management
    "InteractiveSessionManager",
    "EnhancedSessionHandle",
    "ProcessType",
    "ToolResult", 
    "get_session_manager",
    "clean_terminal_output",
    
    # Error recovery
    "ErrorRecoveryManager",
    
    # Monitoring
    "CommandExecutionLogger",
    "PerformanceMonitor",
    # Background notifier
    "BackgroundProcessNotifier",
    "get_background_process_notifier",
    "AsyncTaskMessage",
]


def get_available_process_types():
    """
    Get list of available process types.
    
    Returns:
        dict: Available process types with availability status
    """
    return {
        ProcessType.STANDARD: True,
        ProcessType.PEXPECT: PEXPECT_AVAILABLE
    }


def create_interactive_session(
    command: str,
    process_type: str = "auto",
    **kwargs
):
    """
    Convenience function to create an interactive session.
    
    Args:
        command: Command to execute
        process_type: "auto", "standard", "pexpect"
        **kwargs: Additional session arguments
        
    Returns:
        ToolResult with session information
    """
    manager = get_session_manager()
    
    if process_type == "auto":
        use_pexpect = None
    elif process_type == ProcessType.PEXPECT:
        use_pexpect = True
    elif process_type == ProcessType.STANDARD:
        use_pexpect = False
    else:
        raise ValueError(f"Invalid process type: {process_type}")
    
    return manager.create_session(command, use_pexpect=use_pexpect, **kwargs) 