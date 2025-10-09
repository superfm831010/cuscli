"""
Process manager module for shell command execution.

This module provides process management functionality including:
- Process creation with proper configuration
- Process monitoring and lifecycle management
- Process group management
- Integration with timeout and cleanup systems
"""

import os
import subprocess
import platform
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from loguru import logger

from .timeout_config import TimeoutConfig
from .timeout_manager import TimeoutManager
from .process_cleanup import cleanup_process_tree, get_process_children
from .exceptions import CommandExecutionError, ProcessCleanupError


def _command_to_string(command: Union[str, List[str]]) -> str:
    """
    Convert command to string format for timeout configuration lookup.

    Args:
        command: Command as string or list

    Returns:
        Command as string
    """
    if isinstance(command, list):
        if not command:
            return ""
        # Join list elements into a single string
        return " ".join(str(arg) for arg in command)
    return command


class ProcessManager:
    """
    Manager for process creation and lifecycle management.

    This class handles process creation, monitoring, and cleanup with
    proper timeout management and cross-platform support.
    """

    def __init__(self, config: TimeoutConfig):
        """
        Initialize process manager.

        Args:
            config: Timeout configuration
        """
        self.config = config
        self.timeout_manager = TimeoutManager(config)
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.process_groups: Dict[int, List[int]] = {}
        self.background_processes: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        logger.debug(f"ProcessManager initialized with config: {config}")

    def create_process(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        capture_output: bool = True,
        text: bool = True,
        encoding: str = 'utf-8',
        **kwargs
    ) -> subprocess.Popen:
        """
        Create a new process with proper configuration.

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            capture_output: Whether to capture stdout/stderr
            text: Whether to use text mode
            encoding: Text encoding
            **kwargs: Additional arguments for subprocess.Popen

        Returns:
            Created subprocess.Popen object
        """
        try:
            # Determine timeout
            if timeout is None:
                timeout = self.config.get_timeout_for_command(
                    _command_to_string(command))

            # Prepare process arguments
            popen_args = {
                'shell': shell,
                'cwd': cwd,
                'env': env,
                'text': text,
                'encoding': encoding,
                'errors': 'replace',
                **kwargs
            }

            # Configure output capturing
            if capture_output:
                popen_args.update({
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                })

            # Configure process group creation
            if platform.system() == "Windows":
                popen_args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_args['preexec_fn'] = os.setsid

            logger.debug(f"Creating process for command: {command}")

            # Create process
            process = subprocess.Popen(command, **popen_args)

            # Register process
            self._register_process(process)

            # Note: Timeout will be handled by subprocess.communicate in the executor
            # No need to start separate timeout manager here

            logger.debug(f"Created process with PID {process.pid}")
            return process

        except Exception as e:
            logger.error(
                f"Failed to create process for command '{command}': {e}")
            raise CommandExecutionError(f"Failed to create process: {e}")

    def _register_process(self, process: subprocess.Popen) -> None:
        """Register a process for management."""
        pid = process.pid

        with self._lock:
            self.active_processes[pid] = process

            # Create process group entry
            try:
                if platform.system() != "Windows":
                    pgid = os.getpgid(pid)
                    if pgid not in self.process_groups:
                        self.process_groups[pgid] = []
                    self.process_groups[pgid].append(pid)
                else:
                    # On Windows, each process is its own group
                    self.process_groups[pid] = [pid]
            except OSError:
                pass

        logger.debug(f"Registered process {pid} for management")

    def unregister_process(self, process: subprocess.Popen) -> None:
        """Unregister a process from management."""
        pid = process.pid

        with self._lock:
            # Remove from active processes
            self.active_processes.pop(pid, None)

            # Remove from background processes if it's a background process
            self.background_processes.pop(pid, None)

            # Remove from process groups
            for pgid, pids in list(self.process_groups.items()):
                if pid in pids:
                    pids.remove(pid)
                    if not pids:  # Remove empty groups
                        del self.process_groups[pgid]
                    break

        # Cancel timeout
        self.timeout_manager.cancel_timeout(process)

        logger.debug(f"Unregistered process {pid}")

    def wait_for_process(
        self,
        process: subprocess.Popen,
        timeout: Optional[float] = None
    ) -> int:
        """
        Wait for a process to complete.

        Args:
            process: Process to wait for
            timeout: Timeout in seconds

        Returns:
            Process exit code
        """
        try:
            if timeout:
                exit_code = process.wait(timeout=timeout)
            else:
                exit_code = process.wait()

            # Unregister process
            self.unregister_process(process)

            logger.debug(
                f"Process {process.pid} completed with exit code {exit_code}")
            return exit_code

        except subprocess.TimeoutExpired:
            logger.warning(f"Process {process.pid} timed out during wait")
            raise
        except Exception as e:
            logger.error(f"Error waiting for process {process.pid}: {e}")
            raise CommandExecutionError(f"Error waiting for process: {e}")

    def cleanup_process_tree(
        self,
        process: subprocess.Popen,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Clean up a process and its entire tree.

        Args:
            process: Root process to cleanup
            timeout: Timeout for cleanup

        Returns:
            True if cleanup successful
        """

        try:
            if process.poll() is not None:
                # 进程已经结束，直接注销
                self.unregister_process(process)
                return True
        except Exception as e:
            logger.error(f"Error checking process status: {e}")
            pass

        pid = process.pid

        if timeout is None:
            timeout = self.config.cleanup_timeout

        try:
            logger.debug(f"Cleaning up process tree for PID {pid}")

            # Cancel timeout first
            self.timeout_manager.cancel_timeout(process)

            # Use the process cleanup module
            success = cleanup_process_tree(
                pid,
                timeout=self.config.grace_period,
                force_timeout=timeout - self.config.grace_period
            )

            # Unregister process
            self.unregister_process(process)

            if success:
                logger.debug(
                    f"Successfully cleaned up process tree for PID {pid}")
            else:
                logger.warning(
                    f"Failed to fully cleanup process tree for PID {pid}")

            return success

        except Exception as e:
            logger.error(f"Error cleaning up process tree for PID {pid}: {e}")
            return False

    def get_all_processes(self) -> Dict[int, subprocess.Popen]:
        """Get all active processes."""
        with self._lock:
            return self.active_processes.copy()

    def get_process_groups(self) -> Dict[int, List[int]]:
        """Get process groups mapping."""
        with self._lock:
            return {pgid: pids.copy() for pgid, pids in self.process_groups.items()}

    def cleanup_all_processes(self, timeout: float = 10.0) -> List[int]:
        """
        Clean up all managed processes.

        Args:
            timeout: Timeout for each process cleanup

        Returns:
            List of process IDs that failed to cleanup
        """
        failed_pids = []

        # Get copy of active processes
        with self._lock:
            processes = list(self.active_processes.values())
            background_pids = list(self.background_processes.keys())

        logger.debug(f"Cleaning up {len(processes)} processes (including {len(background_pids)} background processes)")

        for process in processes:
            try:
                if not self.cleanup_process_tree(process, timeout):
                    failed_pids.append(process.pid)
            except Exception as e:
                logger.error(f"Error cleaning up process {process.pid}: {e}")
                failed_pids.append(process.pid)

        # Cleanup timeout manager
        self.timeout_manager.cleanup_all_timeouts()

        # Clear background processes records for successful cleanups
        with self._lock:
            for pid in background_pids:
                if pid not in failed_pids:
                    self.background_processes.pop(pid, None)

        logger.debug(f"Cleanup completed, {len(failed_pids)} processes failed")
        return failed_pids

    def __del__(self):
        """Cleanup when manager is destroyed."""
        try:
            self.cleanup_all_processes()
        except Exception:
            pass  # Ignore errors during cleanup

    def create_background_process(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        process_uniq_id: Optional[str] = None,
        **kwargs
    ) -> subprocess.Popen:
        """
        Create a background process that runs independently.

        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            **kwargs: Additional arguments for subprocess.Popen

        Returns:
            Created subprocess.Popen object for background process
        """
        try:
            # Prepare process arguments for background execution
            popen_args = {
                'shell': shell,
                'cwd': cwd,
                'env': env,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'encoding': 'utf-8',
                'errors': 'replace',
                **kwargs
            }

            # Configure process group creation for proper cleanup
            if platform.system() == "Windows":
                popen_args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_args['preexec_fn'] = os.setsid

            logger.debug(f"Creating background process for command: {command}")

            # Create process
            process = subprocess.Popen(command, **popen_args)

            # Register as background process
            self._register_background_process(process, command, cwd, process_uniq_id)

            logger.debug(f"Created background process with PID {process.pid}")
            return process

        except Exception as e:
            logger.error(
                f"Failed to create background process for command '{command}': {e}")
            raise CommandExecutionError(f"Failed to create background process: {e}")

    def _register_background_process(
        self, 
        process: subprocess.Popen, 
        command: Union[str, List[str]], 
        cwd: Optional[str],
        process_uniq_id: Optional[str] = None
    ) -> None:
        """Register a background process for tracking."""
        pid = process.pid
        command_str = _command_to_string(command)

        # Create backgrounds directory relative to target working directory
        base_dir = cwd if isinstance(cwd, str) and len(cwd) > 0 else os.getcwd()
        backgrounds_dir = os.path.join(base_dir, '.auto-coder', 'backgrounds')
        os.makedirs(backgrounds_dir, exist_ok=True)

        with self._lock:
            # Register in active processes
            self.active_processes[pid] = process

            # Record background process metadata
            self.background_processes[pid] = {
                'command': command_str,
                'cwd': cwd,
                'start_time': time.time(),
                'process': process,
                'process_uniq_id': process_uniq_id
            }

            # Create process group entry
            try:
                if platform.system() != "Windows":
                    pgid = os.getpgid(pid)
                    if pgid not in self.process_groups:
                        self.process_groups[pgid] = []
                    self.process_groups[pgid].append(pid)
                else:
                    # On Windows, each process is its own group
                    self.process_groups[pid] = [pid]
            except OSError:
                pass

        # Start threads to capture stdout and stderr
        self._start_output_capture_threads(process, process_uniq_id or str(pid), backgrounds_dir)

        logger.debug(f"Registered background process {pid} for command: {command_str}")

    def _start_output_capture_threads(
        self, 
        process: subprocess.Popen, 
        process_id: str, 
        backgrounds_dir: str
    ) -> None:
        """Start threads to capture stdout and stderr to files."""
        # Start stdout capture thread
        if process.stdout:
            stdout_file = os.path.join(backgrounds_dir, f"{process_id}.out")
            stdout_thread = threading.Thread(
                target=self._capture_output_to_file,
                args=(process.stdout, stdout_file, process_id, "stdout"),
                daemon=True
            )
            stdout_thread.start()
            logger.debug(f"Started stdout capture thread for process {process_id} (PID {process.pid})")

        # Start stderr capture thread
        if process.stderr:
            stderr_file = os.path.join(backgrounds_dir, f"{process_id}.err")
            stderr_thread = threading.Thread(
                target=self._capture_output_to_file,
                args=(process.stderr, stderr_file, process_id, "stderr"),
                daemon=True
            )
            stderr_thread.start()
            logger.debug(f"Started stderr capture thread for process {process_id} (PID {process.pid})")

    def _capture_output_to_file(
        self, 
        stream, 
        filepath: str, 
        process_id: str, 
        stream_name: str
    ) -> None:
        """Capture output from a stream and write to file.

        Handles both text and binary streams robustly by encoding text to UTF-8
        before writing to the destination file.
        """
        try:
            with open(filepath, 'wb') as f:
                while True:
                    # Read data from stream
                    data = stream.read(4096)
                    if not data:
                        break

                    # Normalize to bytes (stream may be text when Popen(text=True))
                    if isinstance(data, str):
                        data = data.encode('utf-8', errors='replace')

                    # Write to file
                    f.write(data)
                    f.flush()

            logger.debug(f"Finished capturing {stream_name} for process {process_id}")
        except Exception as e:
            logger.error(f"Error capturing {stream_name} for process {process_id}: {e}")
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def get_background_processes(self) -> Dict[int, Dict[str, Any]]:
        """Get all background processes information."""
        with self._lock:
            # Update status for each background process
            updated_processes = {}
            for pid, info in self.background_processes.items():
                process = info['process']
                updated_info = info.copy()
                
                # Update process status
                if process.poll() is None:
                    updated_info['status'] = 'running'
                    updated_info['exit_code'] = None
                else:
                    updated_info['status'] = 'completed'
                    updated_info['exit_code'] = process.returncode
                    updated_info['end_time'] = time.time()
                
                updated_processes[pid] = updated_info
            
            return updated_processes

    def is_background_process(self, pid: int) -> bool:
        """Check if a process is a background process."""
        with self._lock:
            return pid in self.background_processes

    def get_background_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific background process."""
        background_processes = self.get_background_processes()
        return background_processes.get(pid)

    def cleanup_background_process(self, pid: int, timeout: Optional[float] = None) -> bool:
        """
        Clean up a specific background process.

        Args:
            pid: Process ID to cleanup
            timeout: Timeout for cleanup

        Returns:
            True if cleanup successful
        """
        with self._lock:
            if pid not in self.background_processes:
                logger.debug(f"Process {pid} is not a background process")
                return True

            process = self.background_processes[pid]['process']

        # Use the existing cleanup logic
        success = self.cleanup_process_tree(process, timeout)
        
        if success:
            with self._lock:
                # Remove from background processes tracking
                self.background_processes.pop(pid, None)
            
            # Optionally clean up output files
            # For now, we keep them for debugging/audit purposes
            # self._cleanup_output_files(pid)
        
        return success

    def _cleanup_output_files(self, pid: int) -> None:
        """Clean up output files for a background process."""
        # Prefer the background process working directory when available
        with self._lock:
            info = self.background_processes.get(pid)
        if not info:
            return
            
        cwd = info.get('cwd')
        process_uniq_id = info.get('process_uniq_id')
        
        base_dir = cwd if isinstance(cwd, str) and len(cwd) > 0 else os.getcwd()
        backgrounds_dir = os.path.join(base_dir, '.auto-coder', 'backgrounds')
        
        # Use process_uniq_id if available, fallback to pid
        file_prefix = process_uniq_id if process_uniq_id else str(pid)
        stdout_file = os.path.join(backgrounds_dir, f"{file_prefix}.out")
        stderr_file = os.path.join(backgrounds_dir, f"{file_prefix}.err")
        
        for filepath in [stdout_file, stderr_file]:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.debug(f"Removed output file: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to remove output file {filepath}: {e}")

    def get_background_process_count(self) -> int:
        """Get the number of active background processes."""
        with self._lock:
            return len(self.background_processes)
