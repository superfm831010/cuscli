"""
Command executor module for shell command execution with timeout support.

This module provides the main interface for executing shell commands with
comprehensive timeout control, process cleanup, and monitoring capabilities.
"""

import os
import platform
import select
import subprocess
import sys
import time
import threading
from typing import Optional, Dict, Tuple, Any, Generator, Union, List
from loguru import logger as log

from .timeout_config import TimeoutConfig
from .process_manager import ProcessManager, _command_to_string
from .monitoring import CommandExecutionLogger, PerformanceMonitor, get_logger, get_global_monitor
from .error_recovery import ErrorRecoveryManager, create_default_error_recovery_manager
from .exceptions import CommandExecutionError, CommandTimeoutError
from .timeout_manager import create_timeout_context

try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    log.warning("pexpect not available, interactive command support will be limited")
    PEXPECT_AVAILABLE = False


class CommandExecutor:
    """
    Main command executor with timeout support and process management.
    
    This class provides a comprehensive interface for executing shell commands
    with timeout control, process cleanup, monitoring, and error recovery.
    
    Attributes:
        config: Timeout configuration
        process_manager: Process manager instance
        logger: Command execution logger
        monitor: Performance monitor
        error_recovery: Error recovery manager
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
        Initialize command executor.
        
        Args:
            config: Timeout configuration (uses default if None)
            logger: Command execution logger (uses global if None)
            monitor: Performance monitor (uses global if None)
            error_recovery: Error recovery manager (uses default if None)
            verbose: Whether to enable verbose logging
        """
        self.config = config or TimeoutConfig()
        self.process_manager = ProcessManager(self.config)
        self.logger = logger or get_logger(verbose)
        self.monitor = monitor or get_global_monitor()
        self.error_recovery = error_recovery or create_default_error_recovery_manager()
        self.verbose = verbose
        
        log.debug(f"CommandExecutor initialized (verbose={verbose})")
    
    def execute(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        text: bool = True,
        encoding: str = 'utf-8',
        shell: Optional[bool] = None,
        **kwargs
    ) -> Tuple[int, str]:
        """
        Execute a command with timeout support.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (uses config default if None)
            cwd: Working directory
            env: Environment variables
            capture_output: Whether to capture stdout/stderr
            text: Whether to use text mode
            encoding: Text encoding
            shell: Whether to use shell
            **kwargs: Additional arguments for subprocess.Popen
            
        Returns:
            Tuple of (exit_code, output)
            
        Raises:
            CommandTimeoutError: If command times out
            CommandExecutionError: If command execution fails
        """
        # Convert command to string for timeout config and logging
        command_str = _command_to_string(command)
        
        # Determine timeout
        if timeout is None:
            timeout = self.config.get_timeout_for_command(command_str)
        
        # Start logging
        metrics = self.logger.log_command_start(command_str, timeout, cwd=cwd)
        
        # Auto-determine shell parameter if not specified
        if shell is None:
            shell = isinstance(command, str)  # True for strings, False for lists
        
        try:
            # Execute command with subprocess
            exit_code, output = self._execute_with_subprocess(
                command, timeout, cwd, env, capture_output, text, encoding, shell, **kwargs
            )
            
            # Log completion
            self.logger.log_command_complete(metrics, exit_code, output)
            
            # Record metrics
            self.monitor.record_execution(metrics)
            
            return exit_code, output
            
        except Exception as e:
            # Log error
            self.logger.log_command_complete(metrics, -1, "", e)
            
            # Record failed metrics
            self.monitor.record_execution(metrics)
            
            raise
    
    def _execute_with_subprocess(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        capture_output: bool,
        text: bool,
        encoding: str,
        shell: bool,
        **kwargs
    ) -> Tuple[int, str]:
        """
        Execute command using subprocess with timeout support.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            env: Environment variables
            capture_output: Whether to capture output
            text: Whether to use text mode
            encoding: Text encoding
            shell: Whether to use shell
            **kwargs: Additional subprocess arguments
            
        Returns:
            Tuple of (exit_code, output)
        """
        # Create process
        process = self.process_manager.create_process(
            command=command,
            timeout=timeout,
            cwd=cwd,
            env=env,
            shell=shell,
            capture_output=capture_output,
            text=text,
            encoding=encoding,
            **kwargs
        )
        
        # Convert command to string for logging
        command_str = _command_to_string(command)
        metrics = self.logger.log_command_start(command_str, timeout, process.pid, cwd)
        
        # Prepare timeout callback for TimeoutContext
        timeout_occurred = [False]  # Use list to allow modification in nested function
        partial_output = [""]
        
        def timeout_callback(timed_out_process, timeout_val):
            """Handle timeout event with proper logging and cleanup."""
            timeout_occurred[0] = True
            timeout_val = timeout_val if timeout_val is not None else 0.0
            
            # Log timeout
            self.logger.log_command_timeout(metrics, timeout_val, timed_out_process.pid)
            log.warning(f"Command '{command_str}' timed out after {timeout_val} seconds (PID: {timed_out_process.pid})")
            
            # Try to get partial output before cleanup
            try:
                stdout, stderr = timed_out_process.communicate(timeout=2)
                partial_output[0] = stdout or ""
            except:
                partial_output[0] = ""
            
            # The cleanup will be handled by TimeoutContext's cleanup_process_tree
        
        try:
            # Use TimeoutContext for advanced timeout management
            if timeout and timeout > 0:
                with create_timeout_context(process, timeout, callback=timeout_callback):
                    stdout, stderr = process.communicate()  # No timeout here - managed by TimeoutContext
                    
                    # Check if timeout occurred during execution
                    if timeout_occurred[0]:
                        # Use partial output if timeout occurred
                        output_str = partial_output[0]
                        if self.verbose and output_str:
                            print(output_str, end="", flush=True)
                        raise CommandTimeoutError(command_str, timeout, process.pid)
                    
                    output_str = stdout or ""
                    exit_code = process.returncode
            else:
                # No timeout specified, execute normally
                stdout, stderr = process.communicate()
                output_str = stdout or ""
                exit_code = process.returncode
            
            # Handle verbose output
            if self.verbose and output_str:
                print(output_str, end="", flush=True)
            
            if self.verbose:
                log.info(f"Command completed with exit code {exit_code}")
            
            return exit_code, output_str
            
        except Exception as e:
            # Ensure process is cleaned up
            try:
                self.process_manager.cleanup_process_tree(process)
            except Exception as cleanup_error:
                log.error(f"Error during cleanup: {cleanup_error}")
            
            raise e
    
    def execute_generator(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        encoding: str = 'utf-8',
        **kwargs
    ) -> Generator[str, None, int]:
        """
        Execute command and yield output in real-time.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            env: Environment variables
            encoding: Text encoding
            **kwargs: Additional subprocess arguments
            
        Yields:
            Command output strings
            
        Returns:
            Final exit code
            
        Raises:
            CommandTimeoutError: If command times out
            CommandExecutionError: If command execution fails
        """
        # Convert command to string for timeout config and logging
        command_str = _command_to_string(command)
        
        # Determine timeout
        if timeout is None:
            timeout = self.config.get_timeout_for_command(command_str)
        
        # Start logging
        metrics = self.logger.log_command_start(command_str, timeout, cwd=cwd)
        
        try:
            # Create process
            process = self.process_manager.create_process(
                command=command,
                timeout=timeout,
                cwd=cwd,
                env=env,
                shell=True,
                capture_output=True,
                text=True,
                encoding=encoding,
                **kwargs
            )
            
            metrics.pid = process.pid
            
            # Stream output
            output_length = 0
            
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    # Read any remaining output
                    if process.stdout:
                        remaining = process.stdout.read()
                        if remaining:
                            output_length += len(remaining)
                            yield remaining
                    break
                
                # Read output chunk
                if process.stdout:
                    if platform.system() != "Windows":
                        ready, _, _ = select.select([process.stdout], [], [], 0.1)
                        if ready:
                            chunk = process.stdout.read(1024)
                            if chunk:
                                output_length += len(chunk)
                                yield chunk
                    else:
                        try:
                            chunk = process.stdout.read(1024)
                            if chunk:
                                output_length += len(chunk)
                                yield chunk
                        except Exception:
                            pass
                
                time.sleep(0.01)
            
            # Wait for process completion with TimeoutContext
            timeout_occurred = [False]
            
            def generator_timeout_callback(timed_out_process, timeout_val):
                """Handle timeout for generator execution."""
                timeout_occurred[0] = True
                timeout_val = timeout_val if timeout_val is not None else 0.0
                self.logger.log_command_timeout(metrics, timeout_val, timed_out_process.pid)
                log.warning(f"Generator command '{command_str}' timed out after {timeout_val} seconds (PID: {timed_out_process.pid})")
            
            try:
                if timeout and timeout > 0:
                    with create_timeout_context(process, timeout, callback=generator_timeout_callback):
                        exit_code = self.process_manager.wait_for_process(process, None)  # No timeout in wait - managed by TimeoutContext
                        
                        if timeout_occurred[0]:
                            raise CommandTimeoutError(command_str, timeout, process.pid)
                else:
                    exit_code = self.process_manager.wait_for_process(process, None)
            except subprocess.TimeoutExpired:
                # This shouldn't happen with TimeoutContext, but keep as fallback
                timeout_val = timeout if timeout is not None else 0.0
                raise CommandTimeoutError(command_str, timeout_val, process.pid)
            
            # Log completion
            metrics.output_length = output_length
            self.logger.log_command_complete(metrics, exit_code)
            self.monitor.record_execution(metrics)
            
            return exit_code
            
        except Exception as e:
            # Log error
            self.logger.log_command_complete(metrics, -1, "", e)
            self.monitor.record_execution(metrics)
            
            raise
    
    def execute_background(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a command in the background and return immediately with process info.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            **kwargs: Additional arguments for subprocess.Popen
            
        Returns:
            Dictionary containing process information:
            {
                "pid": int,
                "command": str,
                "working_directory": str,
                "start_time": float,
                "status": "running"
            }
            
        Raises:
            CommandExecutionError: If command execution fails
        """
        # Convert command to string for logging
        command_str = _command_to_string(command)
        
        # Start logging
        metrics = self.logger.log_command_start(command_str, None, cwd=cwd)
        
        try:
            # Create background process
            process = self.process_manager.create_background_process(
                command=command,
                cwd=cwd,
                env=env,
                shell=shell,
                **kwargs
            )
            
            # Update metrics with PID
            metrics.pid = process.pid
            
            # Note: We don't log completion here since the process is still running
            # Completion will be logged when the process actually finishes
            
            # Get process info
            process_info = self.process_manager.get_background_process_info(process.pid)
            
            if self.verbose:
                log.info(f"Started background command: {command_str} (PID: {process.pid})")
            
            return {
                "pid": process.pid,
                "command": command_str,
                "working_directory": cwd or os.getcwd(),
                "start_time": process_info["start_time"] if process_info else time.time(),
                "status": "running"
            }
            
        except Exception as e:
            # Log error
            self.logger.log_command_complete(metrics, -1, "", e)
            self.monitor.record_execution(metrics)
            
            raise CommandExecutionError(f"Failed to start background command: {str(e)}")
    
    def get_background_processes(self) -> Dict[int, Dict[str, Any]]:
        """
        Get information about all background processes.
        
        Returns:
            Dictionary mapping PID to process information
        """
        return self.process_manager.get_background_processes()
    
    def get_background_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific background process.
        
        Args:
            pid: Process ID
            
        Returns:
            Process information or None if not found
        """
        return self.process_manager.get_background_process_info(pid)
    
    def cleanup_background_process(self, pid: int, timeout: Optional[float] = None) -> bool:
        """
        Clean up a specific background process.
        
        Args:
            pid: Process ID to cleanup
            timeout: Timeout for cleanup
            
        Returns:
            True if cleanup successful
        """
        return self.process_manager.cleanup_background_process(pid, timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get executor status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            'config': self.config.to_dict(),
            'active_processes': len(self.process_manager.get_all_processes()),
            'background_processes': self.process_manager.get_background_process_count(),
            'process_groups': len(self.process_manager.get_process_groups()),
            'performance_summary': self.monitor.get_performance_summary(),
            'recent_alerts': self.monitor.get_alerts(5),
        }
    
    def execute_batch(
        self,
        commands: List[Union[str, List[str]]],
        timeout: Optional[float] = None,
        per_command_timeout: Optional[float] = None,
        parallel: bool = True,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        text: bool = True,
        encoding: str = 'utf-8',
        shell: Optional[bool] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple commands in batch, either in parallel or serial.
        
        Args:
            commands: List of commands to execute
            timeout: Overall timeout for all commands (seconds)
            per_command_timeout: Timeout for each individual command (seconds)
            parallel: Whether to execute commands in parallel (True) or serial (False)
            cwd: Working directory
            env: Environment variables
            capture_output: Whether to capture stdout/stderr
            text: Whether to use text mode
            encoding: Text encoding
            shell: Whether to use shell
            **kwargs: Additional arguments for subprocess.Popen
            
        Returns:
            List of dictionaries containing results for each command:
            [
                {
                    "command": str,
                    "index": int,
                    "exit_code": int,
                    "output": str,
                    "error": str or None,
                    "timed_out": bool,
                    "duration": float,
                    "start_time": float,
                    "end_time": float
                },
                ...
            ]
            
        Raises:
            CommandExecutionError: If batch execution setup fails
            CommandTimeoutError: If overall timeout is exceeded
        """
        if not commands:
            return []
        
        # Log batch start
        batch_start_time = time.time()
        log.info(f"Starting batch execution of {len(commands)} commands (parallel={parallel})")
        
        # Results list with proper initialization
        results: List[Optional[Dict[str, Any]]] = [None] * len(commands)
        
        # Determine per-command timeout
        if per_command_timeout is None:
            # Use config default or overall timeout divided by command count
            if timeout:
                per_command_timeout = timeout / len(commands) if parallel else timeout
            else:
                per_command_timeout = None  # Will use config default for each command
        
        try:
            if parallel:
                results = self._execute_batch_parallel(
                    commands, timeout, per_command_timeout, cwd, env,
                    capture_output, text, encoding, shell, **kwargs
                )
            else:
                results = self._execute_batch_serial(
                    commands, timeout, per_command_timeout, cwd, env,
                    capture_output, text, encoding, shell, **kwargs
                )
            
            # Log batch completion
            batch_duration = time.time() - batch_start_time
            successful_count = sum(1 for r in results if r and r.get("exit_code") == 0)
            failed_count = sum(1 for r in results if r and r.get("exit_code") != 0)
            timeout_count = sum(1 for r in results if r and r.get("timed_out", False))
            
            log.info(
                f"Batch execution completed in {batch_duration:.2f}s: "
                f"{successful_count} successful, {failed_count} failed, {timeout_count} timed out"
            )
            
            # Ensure all results are non-None before returning
            final_results = []
            for i, r in enumerate(results):
                if r is not None:
                    final_results.append(r)
                else:
                    # This shouldn't happen in normal flow, but handle it
                    final_results.append({
                        "command": _command_to_string(commands[i]),
                        "index": i,
                        "exit_code": -1,
                        "output": "",
                        "error": "Command not executed",
                        "timed_out": False,
                        "duration": 0.0,
                        "start_time": batch_start_time,
                        "end_time": time.time()
                    })
            return final_results
            
        except Exception as e:
            log.error(f"Batch execution failed: {e}")
            # Return partial results if available
            final_results = []
            for i, r in enumerate(results):
                if r is not None:
                    final_results.append(r)
                else:
                    final_results.append({
                        "command": _command_to_string(commands[i]),
                        "index": i,
                        "exit_code": -1,
                        "output": "",
                        "error": str(e),
                        "timed_out": False,
                        "duration": 0.0,
                        "start_time": batch_start_time,
                        "end_time": time.time()
                    })
            return final_results
    
    def _execute_batch_serial(
        self,
        commands: List[Union[str, List[str]]],
        timeout: Optional[float],
        per_command_timeout: Optional[float],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        capture_output: bool,
        text: bool,
        encoding: str,
        shell: bool,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Execute commands serially."""
        results = []
        batch_start = time.time()
        
        for i, command in enumerate(commands):
            # Calculate remaining time if overall timeout is set
            remaining_time = None
            if timeout:
                elapsed = time.time() - batch_start
                remaining_time = timeout - elapsed
                if remaining_time <= 0:
                    # Overall timeout exceeded
                    # Fill remaining results with timeout error
                    for j in range(i, len(commands)):
                        results.append({
                            "command": _command_to_string(commands[j]),
                            "index": j,
                            "exit_code": -1,
                            "output": "",
                            "error": "Batch timeout exceeded before execution",
                            "timed_out": True,
                            "duration": 0.0,
                            "start_time": time.time(),
                            "end_time": time.time()
                        })
                    break
            
            # Use the smaller of per-command timeout and remaining time
            cmd_timeout = per_command_timeout
            if remaining_time is not None:
                cmd_timeout = min(cmd_timeout, remaining_time) if cmd_timeout else remaining_time
            
            # Execute command
            start_time = time.time()
            try:
                exit_code, output = self.execute(
                    command, timeout=cmd_timeout, cwd=cwd, env=env,
                    capture_output=capture_output, text=text, encoding=encoding,
                    shell=shell, **kwargs
                )
                end_time = time.time()
                
                results.append({
                    "command": _command_to_string(command),
                    "index": i,
                    "exit_code": exit_code,
                    "output": output,
                    "error": None,
                    "timed_out": False,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                })
            except CommandTimeoutError as e:
                end_time = time.time()
                results.append({
                    "command": _command_to_string(command),
                    "index": i,
                    "exit_code": -1,
                    "output": "",
                    "error": str(e),
                    "timed_out": True,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                })
            except Exception as e:
                end_time = time.time()
                results.append({
                    "command": _command_to_string(command),
                    "index": i,
                    "exit_code": -1,
                    "output": "",
                    "error": str(e),
                    "timed_out": False,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                })
        
        return results
    
    def _execute_batch_parallel(
        self,
        commands: List[Union[str, List[str]]],
        timeout: Optional[float],
        per_command_timeout: Optional[float],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        capture_output: bool,
        text: bool,
        encoding: str,
        shell: bool,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Execute commands in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import concurrent.futures
        
        results: List[Optional[Dict[str, Any]]] = [None] * len(commands)
        batch_start = time.time()
        
        def execute_single_command(idx: int, cmd: Union[str, List[str]]) -> Tuple[int, Dict[str, Any]]:
            """Execute a single command and return (index, result)."""
            start_time = time.time()
            try:
                exit_code, output = self.execute(
                    cmd, timeout=per_command_timeout, cwd=cwd, env=env,
                    capture_output=capture_output, text=text, encoding=encoding,
                    shell=shell, **kwargs
                )
                end_time = time.time()
                
                return idx, {
                    "command": _command_to_string(cmd),
                    "index": idx,
                    "exit_code": exit_code,
                    "output": output,
                    "error": None,
                    "timed_out": False,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                }
            except CommandTimeoutError as e:
                end_time = time.time()
                return idx, {
                    "command": _command_to_string(cmd),
                    "index": idx,
                    "exit_code": -1,
                    "output": "",
                    "error": str(e),
                    "timed_out": True,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                }
            except Exception as e:
                end_time = time.time()
                return idx, {
                    "command": _command_to_string(cmd),
                    "index": idx,
                    "exit_code": -1,
                    "output": "",
                    "error": str(e),
                    "timed_out": False,
                    "duration": end_time - start_time,
                    "start_time": start_time,
                    "end_time": end_time
                }
        
        # Use ThreadPoolExecutor for parallel execution
        max_workers = min(len(commands), os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all commands
            futures = {
                executor.submit(execute_single_command, i, cmd): i 
                for i, cmd in enumerate(commands)
            }
            
            # Wait for completion with overall timeout
            try:
                # Process completed futures as they finish
                for future in as_completed(futures, timeout=timeout):
                    idx, result = future.result()
                    results[idx] = result
                    
            except concurrent.futures.TimeoutError:
                # Overall timeout exceeded
                log.warning(f"Batch execution timeout exceeded after {timeout}s")
                
                # Cancel remaining futures
                for future in futures:
                    if not future.done():
                        future.cancel()
                
                # Fill in timeout results for uncompleted commands
                for i, result in enumerate(results):
                    if result is None:
                        results[i] = {
                            "command": _command_to_string(commands[i]),
                            "index": i,
                            "exit_code": -1,
                            "output": "",
                            "error": "Batch timeout exceeded",
                            "timed_out": True,
                            "duration": time.time() - batch_start,
                            "start_time": batch_start,
                                                         "end_time": time.time()
                        }
        
        # Ensure all results are non-None before returning
        final_results = []
        for r in results:
            if r is not None:
                final_results.append(r)
        return final_results
    
    def cleanup(self) -> None:
        """
        Clean up all resources and processes.
        """
        log.debug("Cleaning up CommandExecutor")
        
        # Clean up all processes
        failed_pids = self.process_manager.cleanup_all_processes()
        
        if failed_pids:
            log.warning(f"Failed to cleanup {len(failed_pids)} processes: {failed_pids}")
        
        log.debug("CommandExecutor cleanup completed")
    
    def __del__(self):
        """Cleanup when executor is destroyed."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup


# Convenience functions for simple usage
def execute_command(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    verbose: bool = False,
    **kwargs
) -> Tuple[int, str]:
    """
    Convenience function to execute a command with timeout support.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        cwd: Working directory
        verbose: Whether to enable verbose logging
        **kwargs: Additional arguments
        
    Returns:
        Tuple of (exit_code, output)
    """
    # Create a timeout config if timeout is specified
    config = None
    if timeout is not None:
        config = TimeoutConfig(default_timeout=timeout)
    
    executor = CommandExecutor(config=config, verbose=verbose)
    try:
        return executor.execute(command, timeout, cwd, **kwargs)
    finally:
        executor.cleanup()


def execute_command_generator(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    verbose: bool = False,
    **kwargs
) -> Generator[str, None, int]:
    """
    Convenience function to execute a command and stream output.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        cwd: Working directory
        verbose: Whether to enable verbose logging
        **kwargs: Additional arguments
        
    Yields:
        Command output strings
        
    Returns:
        Final exit code
    """
    executor = CommandExecutor(verbose=verbose)
    return executor.execute_generator(command, timeout, cwd, **kwargs)


def execute_command_background(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    verbose: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to execute a command in the background.
    
    Args:
        command: Command to execute
        cwd: Working directory
        verbose: Whether to enable verbose logging
        **kwargs: Additional arguments
        
    Returns:
        Dictionary containing process information with PID
    """
    import uuid
    
    # Use global process manager to maintain background processes
    manager = _get_global_process_manager()
    
    # Convert command to string for logging
    command_str = _command_to_string(command)
    
    # Generate unique process ID
    process_uniq_id = str(uuid.uuid4())
    
    try:
        # Create background process directly with process manager
        process = manager.create_background_process(
            command=command,
            cwd=cwd,
            process_uniq_id=process_uniq_id,
            **kwargs
        )
        
        if verbose:
            log.info(f"Started background command: {command_str} (PID: {process.pid}, ID: {process_uniq_id})")
        
        return {
            "pid": process.pid,
            "process_uniq_id": process_uniq_id,
            "command": command_str,
            "working_directory": cwd or os.getcwd(),
            "start_time": time.time(),
            "status": "running"
        }
        
    except Exception as e:
        raise CommandExecutionError(f"Failed to start background command: {str(e)}")


# Global process manager for background processes
_global_process_manager: Optional[ProcessManager] = None
_global_process_manager_lock = threading.Lock()


def _get_global_process_manager() -> ProcessManager:
    """Get or create global process manager for background processes."""
    global _global_process_manager
    
    if _global_process_manager is None:
        with _global_process_manager_lock:
            if _global_process_manager is None:
                config = TimeoutConfig()
                _global_process_manager = ProcessManager(config)
    
    return _global_process_manager


def get_background_processes() -> Dict[int, Dict[str, Any]]:
    """
    Convenience function to get all background processes.
    
    Returns:
        Dictionary mapping PID to process information
    """
    # Use global process manager to maintain state across calls
    manager = _get_global_process_manager()
    return manager.get_background_processes()


def cleanup_background_process(pid: int, timeout: Optional[float] = None) -> bool:
    """
    Convenience function to cleanup a specific background process.
    
    Args:
        pid: Process ID to cleanup
        timeout: Timeout for cleanup
        
    Returns:
        True if cleanup successful
    """
    # Use global process manager
    manager = _get_global_process_manager()
    return manager.cleanup_background_process(pid, timeout)


def get_background_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get information about a specific background process.
    
    Args:
        pid: Process ID
        
    Returns:
        Process information or None if not found
    """
    # Use global process manager
    manager = _get_global_process_manager()
    return manager.get_background_process_info(pid)


def execute_commands(
    commands: List[Union[str, List[str]]],
    timeout: Optional[float] = None,
    per_command_timeout: Optional[float] = None,
    parallel: bool = True,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    verbose: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Execute multiple commands in batch and return all results.
    
    This is a convenience function that creates a CommandExecutor and executes
    a batch of commands either in parallel or serially.
    
    Args:
        commands: List of commands to execute
        timeout: Overall timeout for all commands (seconds)
        per_command_timeout: Timeout for each individual command (seconds)
        parallel: Whether to execute commands in parallel (True) or serial (False)
        cwd: Working directory
        env: Environment variables
        verbose: Whether to enable verbose logging
        **kwargs: Additional arguments for subprocess.Popen
        
    Returns:
        List of dictionaries containing results for each command:
        [
            {
                "command": str,
                "index": int,
                "exit_code": int,
                "output": str,
                "error": str or None,
                "timed_out": bool,
                "duration": float,
                "start_time": float,
                "end_time": float
            },
            ...
        ]
        
    Raises:
        CommandExecutionError: If batch execution setup fails
        
    Examples:
        >>> # Execute commands in parallel with overall timeout
        >>> results = execute_commands(
        ...     ["echo Hello", "echo World"],
        ...     timeout=10.0,
        ...     parallel=True
        ... )
        >>> for result in results:
        ...     print(f"{result['command']}: {result['output'].strip()}")
        
        >>> # Execute commands serially with per-command timeout
        >>> results = execute_commands(
        ...     ["sleep 1", "echo Done"],
        ...     per_command_timeout=2.0,
        ...     parallel=False
        ... )
    """
    # Create executor with appropriate configuration
    config = TimeoutConfig()
    executor = CommandExecutor(config=config, verbose=verbose)
    
    try:
        # Execute batch
        results = executor.execute_batch(
            commands=commands,
            timeout=timeout,
            per_command_timeout=per_command_timeout,
            parallel=parallel,
            cwd=cwd,
            env=env,
            **kwargs
        )
        return results
    finally:
        # Clean up
        executor.cleanup() 