"""
Interactive command executor for shell command execution.

This module provides interactive command execution functionality including:
- Integration with existing CommandExecutor
- Timeout and monitoring support
- Cross-platform compatibility
- Signal handling and process management
"""

import os
import signal
import threading
import time
import logging
from typing import Optional, Dict, Any, Union, List, Callable

# Set up logger safely
try:
    from loguru import logger as module_logger
except ImportError:
    # Fallback to standard logging if loguru is not available
    module_logger = logging.getLogger(__name__)
    if not module_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        module_logger.addHandler(handler)
        module_logger.setLevel(logging.DEBUG)

from .command_executor import CommandExecutor
from .interactive_process import InteractiveProcess
from .timeout_config import TimeoutConfig
from .monitoring import CommandExecutionLogger, PerformanceMonitor
from .error_recovery import ErrorRecoveryManager
from .exceptions import CommandExecutionError, CommandTimeoutError


class InteractiveSession:
    """
    Interactive session manager for handling multiple interactive processes.
    
    This class manages the lifecycle of interactive sessions, including
    process monitoring, timeout handling, and cleanup.
    """
    
    def __init__(
        self,
        process: InteractiveProcess,
        session_id: str,
        timeout: Optional[float] = None,
        logger: Optional[CommandExecutionLogger] = None,
        monitor: Optional[PerformanceMonitor] = None
    ):
        """
        Initialize interactive session.
        
        Args:
            process: Interactive process instance
            session_id: Unique session identifier
            timeout: Session timeout in seconds
            logger: Command execution logger
            monitor: Performance monitor
        """
        self.process = process
        self.session_id = session_id
        self.timeout = timeout
        self.logger = logger
        self.monitor = monitor
        
        # Session state
        self.start_time = time.time()
        self.last_activity = time.time()
        self.timeout_timer: Optional[threading.Timer] = None
        self.cleanup_callbacks: List[Callable] = []
        
        # Start timeout if specified
        if self.timeout:
            self._start_timeout()
    
    def _start_timeout(self) -> None:
        """Start session timeout timer."""
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        def timeout_handler():
            module_logger.warning(f"Interactive session {self.session_id} timed out after {self.timeout}s")
            self.terminate()
        
        self.timeout_timer = threading.Timer(self.timeout or 0, timeout_handler)
        self.timeout_timer.daemon = True
        self.timeout_timer.start()
    
    def update_activity(self) -> None:
        """Update last activity timestamp and reset timeout."""
        self.last_activity = time.time()
        
        if self.timeout:
            self._start_timeout()
    
    def add_cleanup_callback(self, callback: Callable) -> None:
        """Add cleanup callback to be called when session ends."""
        self.cleanup_callbacks.append(callback)
    
    def terminate(self) -> bool:
        """Terminate the interactive session."""
        try:
            # Cancel timeout
            if self.timeout_timer:
                self.timeout_timer.cancel()
                self.timeout_timer = None
            
            # Terminate process
            success = self.process.terminate()
            
            # Call cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback(self)
                except Exception as e:
                    module_logger.error(f"Error in cleanup callback: {e}")
            
            # Log session stats
            if self.logger:
                stats = self.process.get_stats()
                module_logger.info(f"Interactive session {self.session_id} ended: {stats}")
            
            return success
            
        except Exception as e:
            module_logger.error(f"Error terminating session {self.session_id}: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'duration': time.time() - self.start_time,
            'process_stats': self.process.get_stats(),
            'timeout': self.timeout
        }
    
    def __del__(self) -> None:
        """Destructor - cleanup session."""
        try:
            if self.process.is_alive():
                self.terminate()
        except Exception:
            pass


class InteractiveCommandExecutor:
    """
    Interactive command executor with full integration to shell_commands system.
    
    This class extends the capabilities of CommandExecutor to support
    interactive command execution while maintaining compatibility with
    existing timeout, monitoring, and error recovery systems.
    """
    
    def __init__(
        self,
        config: Optional[TimeoutConfig] = None,
        logger: Optional[CommandExecutionLogger] = None,
        monitor: Optional[PerformanceMonitor] = None,
        error_recovery: Optional[ErrorRecoveryManager] = None,
        verbose: bool = False
    ):
        """
        Initialize interactive command executor.
        
        Args:
            config: Timeout configuration
            logger: Command execution logger
            monitor: Performance monitor
            error_recovery: Error recovery manager
            verbose: Whether to enable verbose logging
        """
        # Initialize base executor for shared functionality
        self.base_executor = CommandExecutor(
            config=config,
            logger=logger,
            monitor=monitor,
            error_recovery=error_recovery,
            verbose=verbose
        )
        
        # Interactive-specific state
        self.active_sessions: Dict[str, InteractiveSession] = {}
        self.session_counter = 0
        self._lock = threading.Lock()
        
        module_logger.debug("InteractiveCommandExecutor initialized")
    
    def execute_interactive(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        use_pty: Optional[bool] = None,
        shell: bool = True,
        encoding: str = 'utf-8',
        session_id: Optional[str] = None,
        **kwargs
    ) -> InteractiveSession:
        """
        Execute a command interactively.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Session timeout (None for no timeout)
            use_pty: Whether to use PTY (auto-detect if None)
            shell: Whether to use shell
            encoding: Text encoding
            session_id: Custom session ID (auto-generated if None)
            **kwargs: Additional arguments
            
        Returns:
            InteractiveSession instance
            
        Raises:
            CommandExecutionError: If command execution fails
        """
        # Generate session ID if not provided
        if session_id is None:
            with self._lock:
                self.session_counter += 1
                session_id = f"session_{self.session_counter}_{int(time.time())}"
        
        # Determine timeout
        if timeout is None:
            # For interactive commands, use interactive_timeout from config
            if hasattr(self.base_executor.config, 'interactive_timeout'):
                timeout = self.base_executor.config.interactive_timeout
        
        try:
            # Create interactive process
            process = InteractiveProcess(
                command=command,
                cwd=cwd,
                env=env,
                use_pty=use_pty,
                shell=shell,
                encoding=encoding,
                **kwargs
            )
            
            # Start the process
            process.start()
            
            # Create session
            session = InteractiveSession(
                process=process,
                session_id=session_id,
                timeout=timeout,
                logger=self.base_executor.logger,
                monitor=self.base_executor.monitor
            )
            
            # Register session
            with self._lock:
                self.active_sessions[session_id] = session
            
            # Add cleanup callback to remove from active sessions
            session.add_cleanup_callback(self._session_cleanup_callback)
            
            module_logger.info(f"Started interactive session {session_id} for command: {command}")
            
            return session
            
        except Exception as e:
            module_logger.error(f"Failed to start interactive session: {e}")
            raise CommandExecutionError(f"Failed to execute interactive command: {e}")
    
    def _session_cleanup_callback(self, session: InteractiveSession) -> None:
        """Cleanup callback for session termination."""
        with self._lock:
            self.active_sessions.pop(session.session_id, None)
        
        module_logger.debug(f"Cleaned up session {session.session_id}")
    
    def get_session(self, session_id: str) -> Optional[InteractiveSession]:
        """Get active session by ID."""
        with self._lock:
            return self.active_sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        with self._lock:
            return [session.get_session_stats() for session in self.active_sessions.values()]
    
    def terminate_session(self, session_id: str) -> bool:
        """Terminate a specific session."""
        session = self.get_session(session_id)
        if session:
            return session.terminate()
        return False
    
    def terminate_all_sessions(self) -> Dict[str, bool]:
        """Terminate all active sessions."""
        results = {}
        
        with self._lock:
            sessions = list(self.active_sessions.values())
        
        for session in sessions:
            try:
                results[session.session_id] = session.terminate()
            except Exception as e:
                module_logger.error(f"Error terminating session {session.session_id}: {e}")
                results[session.session_id] = False
        
        return results
    
    def send_signal_to_session(self, session_id: str, sig: int) -> bool:
        """Send signal to a specific session."""
        session = self.get_session(session_id)
        if session and session.process.is_alive():
            try:
                session.process.send_signal(sig)
                session.update_activity()
                return True
            except Exception as e:
                module_logger.error(f"Error sending signal to session {session_id}: {e}")
                return False
        return False
    
    def send_interrupt_to_session(self, session_id: str) -> bool:
        """Send interrupt signal (Ctrl+C) to a specific session."""
        return self.send_signal_to_session(session_id, signal.SIGINT)
    
    def write_to_session(self, session_id: str, data: str) -> bool:
        """Write data to a specific session."""
        session = self.get_session(session_id)
        if session and session.process.is_alive():
            try:
                session.process.write(data)
                session.update_activity()
                return True
            except Exception as e:
                module_logger.error(f"Error writing to session {session_id}: {e}")
                return False
        return False
    
    def read_from_session(
        self, 
        session_id: str, 
        timeout: Optional[float] = None
    ) -> Optional[str]:
        """Read output from a specific session."""
        session = self.get_session(session_id)
        if session:
            try:
                data = session.process.read_output(timeout=timeout)
                if data:
                    session.update_activity()
                return data
            except Exception as e:
                module_logger.error(f"Error reading from session {session_id}: {e}")
                return None
        return None
    
    def get_executor_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        with self._lock:
            active_count = len(self.active_sessions)
            sessions_stats = [s.get_session_stats() for s in self.active_sessions.values()]
        
        return {
            'active_sessions': active_count,
            'total_sessions_created': self.session_counter,
            'base_executor_stats': self.base_executor.get_status(),
            'sessions': sessions_stats
        }
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        module_logger.debug("Cleaning up InteractiveCommandExecutor")
        
        # Terminate all sessions
        self.terminate_all_sessions()
        
        # Clean up base executor
        self.base_executor.cleanup()
        
        module_logger.debug("InteractiveCommandExecutor cleanup completed")
    
    def __del__(self) -> None:
        """Destructor - cleanup when executor is destroyed."""
        try:
            self.cleanup()
        except Exception:
            pass


# Convenience functions for simple usage
def execute_interactive(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    use_pty: Optional[bool] = None,
    verbose: bool = False,
    **kwargs
) -> InteractiveSession:
    """
    Convenience function to execute a command interactively.
    
    Args:
        command: Command to execute
        cwd: Working directory
        env: Environment variables
        timeout: Session timeout
        use_pty: Whether to use PTY
        verbose: Whether to enable verbose logging
        **kwargs: Additional arguments
        
    Returns:
        InteractiveSession instance
    """
    executor = InteractiveCommandExecutor(verbose=verbose)
    
    try:
        return executor.execute_interactive(
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            use_pty=use_pty,
            **kwargs
        )
    except Exception:
        executor.cleanup()
        raise


def create_interactive_shell(
    shell_command: Optional[str] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> InteractiveSession:
    """
    Create an interactive shell session.
    
    Args:
        shell_command: Shell command to execute (auto-detect if None)
        cwd: Working directory
        env: Environment variables
        timeout: Session timeout
        **kwargs: Additional arguments
        
    Returns:
        InteractiveSession instance
    """
    if shell_command is None:
        # Auto-detect shell
        import platform
        if platform.system() == "Windows":
            shell_command = "cmd"
        else:
            shell_command = os.environ.get("SHELL", "/bin/bash")
    
    return execute_interactive(
        command=shell_command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        use_pty=True,  # Prefer PTY for shell
        **kwargs
    ) 