"""
Timeout manager module for shell command execution.

This module provides timeout management functionality including:
- Starting and canceling timeouts
- Handling timeout events
- Managing multiple concurrent timeouts
- Integration with process cleanup
"""

import subprocess
import threading
import time
from typing import Dict, Optional, Callable
from loguru import logger

from .timeout_config import TimeoutConfig
from .process_cleanup import cleanup_process_tree
from .exceptions import CommandTimeoutError


class TimeoutManager:
    """
    Manager for command execution timeouts.
    
    This class handles timeout management for command execution, including
    starting timers, canceling them, and handling timeout events with
    proper process cleanup.
    
    Attributes:
        config: Timeout configuration
        active_timers: Dictionary of active timeout timers
        timeout_callbacks: Dictionary of timeout callbacks
    """
    
    def __init__(self, config: TimeoutConfig):
        """
        Initialize timeout manager.
        
        Args:
            config: Timeout configuration to use
        """
        self.config = config
        self.active_timers: Dict[int, threading.Timer] = {}
        self.timeout_callbacks: Dict[int, Callable] = {}
        self._lock = threading.Lock()
        
        logger.debug(f"TimeoutManager initialized with config: {config}")
    
    def start_timeout(
        self, 
        process: subprocess.Popen, 
        timeout: float,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Start a timeout for a process.
        
        Args:
            process: The subprocess.Popen object to monitor
            timeout: Timeout duration in seconds
            callback: Optional callback to call on timeout (in addition to cleanup)
        """
        if timeout <= 0:
            logger.warning(f"Invalid timeout value: {timeout}, ignoring")
            return
        
        pid = process.pid
        
        with self._lock:
            # Cancel any existing timeout for this process (without acquiring lock again)
            existing_timer = self.active_timers.pop(pid, None)
            existing_callback = self.timeout_callbacks.pop(pid, None)
            
            if existing_timer:
                existing_timer.cancel()
                logger.debug(f"Canceled existing timeout for PID {pid}")
            
            # Create timeout handler
            def timeout_handler():
                self._handle_timeout(process, timeout, callback)
            
            # Start timer
            timer = threading.Timer(timeout, timeout_handler)
            timer.daemon = True  # Don't prevent program exit
            
            try:
                timer.start()
                
                # Store timer and callback only if start was successful
                self.active_timers[pid] = timer
                if callback:
                    self.timeout_callbacks[pid] = callback
                
                logger.debug(f"Started timeout for PID {pid} with {timeout}s timeout")
                
            except Exception as e:
                logger.error(f"Failed to start timeout for PID {pid}: {e}")
                # Don't store the timer since it failed to start
    
    def cancel_timeout(self, process: subprocess.Popen) -> bool:
        """
        Cancel timeout for a process.
        
        Args:
            process: The subprocess.Popen object
            
        Returns:
            True if timeout was canceled, False if no timeout was active
        """
        pid = process.pid
        
        with self._lock:
            timer = self.active_timers.pop(pid, None)
            callback = self.timeout_callbacks.pop(pid, None)
            
            if timer:
                timer.cancel()
                logger.debug(f"Canceled timeout for PID {pid}")
                return True
            
            return False
    
    def is_timeout_active(self, process: subprocess.Popen) -> bool:
        """
        Check if timeout is active for a process.
        
        Args:
            process: The subprocess.Popen object
            
        Returns:
            True if timeout is active
        """
        pid = process.pid
        with self._lock:
            return pid in self.active_timers
    
    def get_remaining_timeout(self, process: subprocess.Popen) -> Optional[float]:
        """
        Get remaining timeout for a process.
        
        Args:
            process: The subprocess.Popen object
            
        Returns:
            Remaining timeout in seconds, or None if no timeout active
        """
        pid = process.pid
        with self._lock:
            timer = self.active_timers.get(pid)
            if timer and timer.is_alive():
                # This is an approximation since Timer doesn't expose remaining time
                # In practice, this would need more sophisticated tracking
                return None  # Could implement if needed
            return None
    
    def _handle_timeout(
        self, 
        process: subprocess.Popen, 
        timeout: float,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Handle timeout event for a process.
        
        Args:
            process: The subprocess.Popen object that timed out
            timeout: The timeout value that was exceeded
            callback: Optional user callback to execute
        """
        pid = process.pid
        
        logger.warning(f"Process {pid} timed out after {timeout} seconds")
        
        try:
            # Remove from active timers
            with self._lock:
                self.active_timers.pop(pid, None)
                self.timeout_callbacks.pop(pid, None)
            
            # Execute user callback if provided
            if callback:
                try:
                    callback(process, timeout)
                except Exception as e:
                    logger.error(f"Error in timeout callback for PID {pid}: {e}")
            
            # Attempt to cleanup the process tree
            try:
                cleanup_success = cleanup_process_tree(
                    pid, 
                    timeout=self.config.grace_period,
                    force_timeout=self.config.cleanup_timeout - self.config.grace_period
                )
                
                if cleanup_success:
                    logger.debug(f"Successfully cleaned up process tree for PID {pid}")
                else:
                    logger.warning(f"Failed to fully cleanup process tree for PID {pid}")
                    
            except Exception as e:
                logger.error(f"Error during process cleanup for PID {pid}: {e}")
        
        except Exception as e:
            logger.error(f"Error handling timeout for PID {pid}: {e}")
    
    def cleanup_all_timeouts(self) -> None:
        """
        Cancel all active timeouts.
        
        This method should be called when shutting down to ensure
        all timers are properly canceled.
        """
        with self._lock:
            for pid, timer in self.active_timers.items():
                try:
                    timer.cancel()
                    logger.debug(f"Canceled timeout for PID {pid} during cleanup")
                except Exception as e:
                    logger.error(f"Error canceling timeout for PID {pid}: {e}")
            
            self.active_timers.clear()
            self.timeout_callbacks.clear()
            
        logger.debug("All timeouts cleaned up")
    
    def get_active_timeouts(self) -> Dict[int, bool]:
        """
        Get information about active timeouts.
        
        Returns:
            Dictionary mapping PID to timer status (alive/dead)
        """
        with self._lock:
            return {
                pid: timer.is_alive() 
                for pid, timer in self.active_timers.items()
            }
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        try:
            self.cleanup_all_timeouts()
        except Exception:
            pass  # Ignore errors during cleanup


class TimeoutContext:
    """
    Context manager for timeout management.
    
    This provides a convenient way to manage timeouts using the 'with' statement.
    The timeout is automatically canceled when exiting the context.
    """
    
    def __init__(
        self, 
        manager: TimeoutManager, 
        process: subprocess.Popen, 
        timeout: float,
        callback: Optional[Callable] = None
    ):
        """
        Initialize timeout context.
        
        Args:
            manager: TimeoutManager instance
            process: Process to monitor
            timeout: Timeout duration
            callback: Optional timeout callback
        """
        self.manager = manager
        self.process = process
        self.timeout = timeout
        self.callback = callback
    
    def __enter__(self) -> 'TimeoutContext':
        """Start timeout when entering context."""
        self.manager.start_timeout(self.process, self.timeout, self.callback)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cancel timeout when exiting context."""
        self.manager.cancel_timeout(self.process)


class GlobalTimeoutManager:
    """
    Global singleton timeout manager.
    
    This provides a convenient way to access a global timeout manager
    throughout the application.
    """
    
    _instance: Optional[TimeoutManager] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, config: Optional[TimeoutConfig] = None) -> TimeoutManager:
        """
        Get or create the global timeout manager instance.
        
        Args:
            config: Optional config to use for first initialization
            
        Returns:
            Global TimeoutManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        config = TimeoutConfig()
                    cls._instance = TimeoutManager(config)
                    logger.debug("Created global TimeoutManager instance")
        
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the global instance.
        
        This is mainly useful for testing.
        """
        with cls._lock:
            if cls._instance:
                cls._instance.cleanup_all_timeouts()
            cls._instance = None
            logger.debug("Reset global TimeoutManager instance")


def create_timeout_context(
    process: subprocess.Popen, 
    timeout: float,
    config: Optional[TimeoutConfig] = None,
    callback: Optional[Callable] = None
) -> TimeoutContext:
    """
    Convenience function to create a timeout context.
    
    Args:
        process: Process to monitor
        timeout: Timeout duration
        config: Optional timeout configuration
        callback: Optional timeout callback
        
    Returns:
        TimeoutContext instance
    """
    manager = GlobalTimeoutManager.get_instance(config)
    return TimeoutContext(manager, process, timeout, callback) 