"""
Monitoring module for shell command execution.

This module provides comprehensive monitoring functionality including:
- Command execution logging
- Performance monitoring
- Metrics collection
- Error tracking
"""

import time
import threading
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .exceptions import CommandExecutionError, CommandTimeoutError


@dataclass
class CommandExecutionMetrics:
    """
    Metrics for command execution.
    
    Attributes:
        command: The executed command
        start_time: Execution start time
        end_time: Execution end time
        duration: Total execution duration in seconds
        exit_code: Process exit code
        timeout: Configured timeout (if any)
        timed_out: Whether the command timed out
        pid: Process ID
        output_length: Length of command output
        error_count: Number of errors encountered
        recovery_attempts: Number of recovery attempts made
    """
    command: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    exit_code: Optional[int] = None
    timeout: Optional[float] = None
    timed_out: bool = False
    pid: Optional[int] = None
    output_length: int = 0
    error_count: int = 0
    recovery_attempts: int = 0
    
    def finalize(self, end_time: Optional[datetime] = None) -> None:
        """
        Finalize metrics calculation.
        
        Args:
            end_time: Optional end time, defaults to current time
        """
        if end_time is None:
            end_time = datetime.now()
        
        self.end_time = end_time
        self.duration = (end_time - self.start_time).total_seconds()


class CommandExecutionLogger:
    """
    Logger for command execution events.
    
    This class provides structured logging for command execution with
    configurable verbosity levels and output formatting.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize command execution logger.
        
        Args:
            verbose: Whether to enable verbose logging
        """
        self.verbose = verbose
        self.execution_history: List[CommandExecutionMetrics] = []
        self._lock = threading.Lock()
        
        logger.debug(f"CommandExecutionLogger initialized (verbose={verbose})")
    
    def log_command_start(
        self,
        command: str,
        timeout: Optional[float] = None,
        pid: Optional[int] = None,
        cwd: Optional[str] = None
    ) -> CommandExecutionMetrics:
        """
        Log command execution start.
        
        Args:
            command: The command being executed
            timeout: Timeout configuration
            pid: Process ID
            cwd: Working directory
            
        Returns:
            CommandExecutionMetrics instance for this execution
        """
        metrics = CommandExecutionMetrics(
            command=command,
            start_time=datetime.now(),
            timeout=timeout,
            pid=pid
        )
        
        with self._lock:
            self.execution_history.append(metrics)
        
        if self.verbose:
            logger.info(f"Starting command execution: {command}")
            if timeout:
                logger.info(f"  Timeout: {timeout}s")
            if pid:
                logger.info(f"  PID: {pid}")
            if cwd:
                logger.info(f"  Working directory: {cwd}")
        else:
            logger.debug(f"Starting command: {command} (PID: {pid})")
        
        return metrics
    
    def log_command_complete(
        self,
        metrics: CommandExecutionMetrics,
        exit_code: int,
        output: str = "",
        error: Optional[Exception] = None
    ) -> None:
        """
        Log command execution completion.
        
        Args:
            metrics: Execution metrics
            exit_code: Process exit code
            output: Command output
            error: Any error that occurred
        """
        metrics.exit_code = exit_code
        metrics.output_length = len(output)
        if error:
            metrics.error_count += 1
            # Check if it's a timeout error
            if isinstance(error, CommandTimeoutError):
                metrics.timed_out = True
        
        metrics.finalize()
        
        if self.verbose:
            logger.info(f"Command completed: {metrics.command}")
            logger.info(f"  Exit code: {exit_code}")
            logger.info(f"  Duration: {metrics.duration:.2f}s")
            logger.info(f"  Output length: {metrics.output_length} characters")
            if error:
                logger.warning(f"  Error: {error}")
        else:
            status = "SUCCESS" if exit_code == 0 else "FAILED"
            logger.debug(f"Command {status}: {metrics.command} ({metrics.duration:.2f}s)")
        
        # Log performance warnings
        if metrics.duration and metrics.duration > 30.0:
            logger.warning(f"Long-running command: {metrics.command} took {metrics.duration:.2f}s")
        
        if metrics.timeout and metrics.duration and metrics.duration > metrics.timeout * 0.8:
            logger.warning(f"Command approaching timeout: {metrics.command} ({metrics.duration:.2f}s/{metrics.timeout}s)")
    
    def log_command_timeout(
        self,
        metrics: CommandExecutionMetrics,
        timeout: float,
        pid: int
    ) -> None:
        """
        Log command timeout event.
        
        Args:
            metrics: Execution metrics
            timeout: Timeout value that was exceeded
            pid: Process ID that timed out
        """
        metrics.timed_out = True
        metrics.finalize()
        
        logger.error(f"Command timed out: {metrics.command}")
        logger.error(f"  Timeout: {timeout}s")
        logger.error(f"  PID: {pid}")
        logger.error(f"  Actual duration: {metrics.duration:.2f}s")
    
    def log_process_cleanup(
        self,
        pid: int,
        success: bool,
        duration: float,
        method: str = "unknown"
    ) -> None:
        """
        Log process cleanup event.
        
        Args:
            pid: Process ID that was cleaned up
            success: Whether cleanup was successful
            duration: Cleanup duration in seconds
            method: Cleanup method used
        """
        if success:
            logger.debug(f"Process cleanup successful: PID {pid} ({method}, {duration:.2f}s)")
        else:
            logger.warning(f"Process cleanup failed: PID {pid} ({method}, {duration:.2f}s)")
    
    def log_error_recovery(
        self,
        error: Exception,
        recovery_attempt: int,
        success: bool
    ) -> None:
        """
        Log error recovery attempt.
        
        Args:
            error: The error being recovered from
            recovery_attempt: Recovery attempt number
            success: Whether recovery was successful
        """
        error_type = type(error).__name__
        
        if success:
            logger.info(f"Error recovery successful: {error_type} (attempt {recovery_attempt})")
        else:
            logger.warning(f"Error recovery failed: {error_type} (attempt {recovery_attempt})")
    
    def get_execution_history(self) -> List[CommandExecutionMetrics]:
        """
        Get command execution history.
        
        Returns:
            List of execution metrics
        """
        with self._lock:
            return self.execution_history.copy()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for command executions.
        
        Returns:
            Dictionary with summary statistics
        """
        with self._lock:
            history = self.execution_history.copy()
        
        if not history:
            return {}
        
        completed = [m for m in history if m.duration is not None]
        successful = [m for m in completed if m.exit_code == 0]
        failed = [m for m in completed if m.exit_code != 0 and not m.timed_out]
        timed_out = [m for m in history if m.timed_out]
        
        # Get durations that are not None for calculations
        durations = [m.duration for m in completed if m.duration is not None]
        total_duration = sum(durations)
        avg_duration = total_duration / len(durations) if durations else 0
        
        return {
            'total_commands': len(history),
            'completed_commands': len(completed),
            'successful_commands': len(successful),
            'failed_commands': len(failed),
            'timed_out_commands': len(timed_out),
            'success_rate': len(successful) / len(completed) if completed else 0,
            'timeout_rate': len(timed_out) / len(history) if history else 0,
            'total_duration': total_duration,
            'average_duration': avg_duration,
            'max_duration': max(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
        }


class PerformanceMonitor:
    """
    Performance monitor for command execution.
    
    This class tracks performance metrics and provides analysis
    of command execution patterns and performance trends.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_history_size: Maximum number of metrics to keep in history
        """
        self.max_history_size = max_history_size
        self.metrics_history: List[CommandExecutionMetrics] = []
        self.performance_alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        logger.debug(f"PerformanceMonitor initialized (max_history={max_history_size})")
    
    def record_execution(self, metrics: CommandExecutionMetrics) -> None:
        """
        Record command execution metrics.
        
        Args:
            metrics: Execution metrics to record
        """
        with self._lock:
            self.metrics_history.append(metrics)
            
            # Trim history if too large
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # Check for performance issues
        self._check_performance_alerts(metrics)
    
    def _check_performance_alerts(self, metrics: CommandExecutionMetrics) -> None:
        """
        Check for performance issues and generate alerts.
        
        Args:
            metrics: Execution metrics to check
        """
        alerts = []
        
        # Check for long execution times
        if metrics.duration and metrics.duration > 60.0:
            alerts.append({
                'type': 'long_execution',
                'message': f"Command took {metrics.duration:.2f}s to execute",
                'command': metrics.command,
                'duration': metrics.duration
            })
        
        # Check for timeout
        if metrics.timed_out:
            alerts.append({
                'type': 'timeout',
                'message': f"Command timed out after {metrics.timeout}s",
                'command': metrics.command,
                'timeout': metrics.timeout
            })
        
        # Check for high error rate
        recent_metrics = self.get_recent_metrics(10)
        if len(recent_metrics) >= 5:
            error_rate = sum(1 for m in recent_metrics if m.error_count > 0) / len(recent_metrics)
            if error_rate > 0.5:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f"High error rate detected: {error_rate:.1%}",
                    'error_rate': error_rate
                })
        
        # Store alerts
        if alerts:
            with self._lock:
                self.performance_alerts.extend(alerts)
                # Keep only recent alerts
                self.performance_alerts = self.performance_alerts[-100:]
            
            for alert in alerts:
                logger.warning(f"Performance alert: {alert['message']}")
    
    def get_recent_metrics(self, count: int = 10) -> List[CommandExecutionMetrics]:
        """
        Get recent command execution metrics.
        
        Args:
            count: Number of recent metrics to return
            
        Returns:
            List of recent metrics
        """
        with self._lock:
            return self.metrics_history[-count:]
    
    def get_command_stats(self, command_pattern: str) -> Dict[str, Any]:
        """
        Get statistics for commands matching a pattern.
        
        Args:
            command_pattern: Pattern to match commands against
            
        Returns:
            Dictionary with command statistics
        """
        with self._lock:
            matching_metrics = [
                m for m in self.metrics_history
                if command_pattern in m.command
            ]
        
        if not matching_metrics:
            return {}
        
        completed = [m for m in matching_metrics if m.duration is not None]
        successful = [m for m in completed if m.exit_code == 0]
        
        durations = [m.duration for m in completed if m.duration is not None]
        
        return {
            'total_executions': len(matching_metrics),
            'completed_executions': len(completed),
            'successful_executions': len(successful),
            'success_rate': len(successful) / len(completed) if completed else 0,
            'average_duration': sum(durations) / len(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'total_duration': sum(durations),
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        with self._lock:
            total_metrics = len(self.metrics_history)
            alerts = len(self.performance_alerts)
            
            if not self.metrics_history:
                return {'total_commands': 0, 'alerts': 0}
            
            recent_metrics = self.metrics_history[-50:]  # Last 50 commands
            
            completed = [m for m in recent_metrics if m.duration is not None]
            successful = [m for m in completed if m.exit_code == 0]
            timed_out = [m for m in recent_metrics if m.timed_out]
            
            durations = [m.duration for m in completed if m.duration is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_commands': total_metrics,
                'recent_commands': len(recent_metrics),
                'success_rate': len(successful) / len(completed) if completed else 0,
                'timeout_rate': len(timed_out) / len(recent_metrics) if recent_metrics else 0,
                'average_duration': avg_duration,
                'performance_alerts': alerts,
                'longest_command': max(durations) if durations else 0,
                'shortest_command': min(durations) if durations else 0,
            }
    
    def get_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent performance alerts.
        
        Args:
            count: Number of alerts to return
            
        Returns:
            List of recent alerts
        """
        with self._lock:
            return self.performance_alerts[-count:]
    
    def clear_alerts(self) -> None:
        """Clear all performance alerts."""
        with self._lock:
            self.performance_alerts.clear()
        
        logger.debug("Performance alerts cleared")


# Global instances
_global_logger: Optional[CommandExecutionLogger] = None
_global_monitor: Optional[PerformanceMonitor] = None
_global_lock = threading.Lock()


def get_logger(verbose: bool = False) -> CommandExecutionLogger:
    """
    Get global logger instance.
    
    Args:
        verbose: Whether to enable verbose logging
        
    Returns:
        Global logger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = CommandExecutionLogger(verbose=verbose)
    else:
        # Update verbose flag if different
        if _global_logger.verbose != verbose:
            _global_logger.verbose = verbose
    
    return _global_logger


def get_global_monitor() -> PerformanceMonitor:
    """
    Get or create global performance monitor.
    
    Returns:
        Global PerformanceMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        with _global_lock:
            if _global_monitor is None:
                _global_monitor = PerformanceMonitor()
    
    return _global_monitor


def reset_global_instances() -> None:
    """
    Reset global logger and monitor instances.
    
    This is mainly useful for testing.
    """
    global _global_logger, _global_monitor
    
    with _global_lock:
        _global_logger = None
        _global_monitor = None 