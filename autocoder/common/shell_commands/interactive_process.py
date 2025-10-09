"""
Interactive process wrapper for shell command execution.

This module provides interactive process functionality including:
- Real-time input/output streaming
- Cross-platform PTY/pipe support
- Signal handling (Ctrl-C, etc.)
- Thread-safe operations
"""

import os
import platform
import subprocess
import threading
import time
import queue
import select
import signal
from typing import Optional, Dict, Any, Generator, Union, List
from loguru import logger

from .exceptions import CommandExecutionError, ProcessCleanupError
from .process_cleanup import cleanup_process_tree

# Platform-specific imports
PLATFORM = platform.system()
PTY_AVAILABLE = False
WINPTY_AVAILABLE = False

try:
    if PLATFORM != "Windows":
        import pty
        import termios
        import fcntl
        PTY_AVAILABLE = True
except ImportError:
    logger.debug("PTY not available on this platform")

try:
    if PLATFORM == "Windows":
        import winpty  # type: ignore
        WINPTY_AVAILABLE = True
except ImportError:
    logger.debug("winpty not available, falling back to pipes")


class InteractiveProcess:
    """
    Interactive process wrapper for real-time command execution.
    
    This class provides a convenient interface for executing commands that
    require interactive input/output, supporting both PTY and pipe modes
    across different platforms.
    """
    
    def __init__(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        use_pty: Optional[bool] = None,
        shell: bool = True,
        encoding: str = 'utf-8',
        **kwargs
    ):
        """
        Initialize interactive process.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            use_pty: Whether to use PTY (auto-detect if None)
            shell: Whether to use shell
            encoding: Text encoding
            **kwargs: Additional subprocess arguments
        """
        self.command = command
        self.cwd = cwd
        self.env = env
        self.encoding = encoding
        self.shell = shell
        
        # Determine if we should use PTY
        if use_pty is None:
            self.use_pty = PTY_AVAILABLE and PLATFORM != "Windows"
        else:
            self.use_pty = use_pty and PTY_AVAILABLE
        
        # State management
        self.process: Optional[subprocess.Popen] = None
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.winpty_process = None
        
        # Threading
        self.output_queue: queue.Queue = queue.Queue()
        self.error_queue: queue.Queue = queue.Queue()
        self.io_thread: Optional[threading.Thread] = None
        self.alive_event = threading.Event()
        self.started_event = threading.Event()
        
        # Monitoring
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.bytes_written = 0
        self.bytes_read = 0
        
        logger.debug(f"InteractiveProcess initialized: use_pty={self.use_pty}, platform={PLATFORM}")
    
    def start(self) -> None:
        """Start the interactive process."""
        if self.is_alive():
            raise CommandExecutionError("Process is already running")
        
        self.start_time = time.time()
        self.alive_event.set()
        
        try:
            if self.use_pty:
                self._start_with_pty()
            elif PLATFORM == "Windows" and WINPTY_AVAILABLE:
                self._start_with_winpty()
            else:
                self._start_with_pipes()
            
            # Start I/O thread
            self.io_thread = threading.Thread(target=self._io_worker, daemon=True)
            self.io_thread.start()
            
            # Give process a moment to start and check if it's valid
            time.sleep(0.1)
            
            # Check if process failed immediately (e.g., command not found)
            if not self.is_alive():
                exit_code = self.exit_code
                if exit_code is not None and exit_code != 0:
                    self._cleanup()
                    raise CommandExecutionError(f"Interactive process failed to start: exit code {exit_code}")
            
            self.started_event.set()
            logger.info(f"Interactive process started: PID {self.pid}")
            
        except Exception as e:
            self.alive_event.clear()
            self._cleanup()
            raise CommandExecutionError(f"Failed to start interactive process: {e}")
    
    def _start_with_pty(self) -> None:
        """Start process with PTY (Linux/Mac)."""
        if not PTY_AVAILABLE:
            raise CommandExecutionError("PTY not available on this platform")
        
        # Create PTY
        self.master_fd, self.slave_fd = pty.openpty()
        
        # Configure PTY
        try:
            # Get current terminal settings
            attrs = termios.tcgetattr(self.slave_fd)
            
            # Disable echo to avoid duplicate output
            attrs[3] = attrs[3] & ~termios.ECHO
            
            # Set raw mode for better control
            attrs[3] = attrs[3] & ~(termios.ICANON | termios.ISIG)
            
            termios.tcsetattr(self.slave_fd, termios.TCSANOW, attrs)
            
            # Make master non-blocking
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, os.O_NONBLOCK)
            
        except Exception as e:
            logger.warning(f"Failed to configure PTY: {e}")
        
        # Start process with PTY
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                cwd=self.cwd,
                env=self.env,
                shell=self.shell,
                start_new_session=True  # This automatically calls setsid(), so no need for preexec_fn
            )
        except Exception as e:
            # If process creation fails, clean up PTY fds
            if self.master_fd is not None:
                os.close(self.master_fd)
                self.master_fd = None
            if self.slave_fd is not None:
                os.close(self.slave_fd)
                self.slave_fd = None
            raise CommandExecutionError(f"Failed to start PTY process: {e}")
    
    def _start_with_winpty(self) -> None:
        """Start process with winpty (Windows)."""
        if not WINPTY_AVAILABLE:
            raise CommandExecutionError("winpty not available")
        
        try:
            # Convert command to string if needed
            if isinstance(self.command, list):
                cmd_str = ' '.join(self.command)
            else:
                cmd_str = self.command
            
            # Create winpty process
            self.winpty_process = winpty.PtyProcess.spawn(
                cmd_str,
                cwd=self.cwd,
                env=self.env
            )
            
            # Create a subprocess wrapper for compatibility
            winpty_proc = self.winpty_process  # Capture for closure
            self.process = type('MockProcess', (), {
                'pid': winpty_proc.pid,
                'poll': lambda: winpty_proc.exitstatus if not winpty_proc.isalive() else None,
                'wait': lambda timeout=None: winpty_proc.wait(),
                'terminate': lambda: winpty_proc.terminate(),
                'kill': lambda: winpty_proc.terminate(force=True),
                'returncode': property(lambda s: winpty_proc.exitstatus)
            })()  # type: ignore
            
        except Exception as e:
            raise CommandExecutionError(f"Failed to start winpty process: {e}")
    
    def _start_with_pipes(self) -> None:
        """Start process with regular pipes."""
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=self.env,
            shell=self.shell,
            text=True,
            encoding=self.encoding,
            bufsize=0,  # Unbuffered
            universal_newlines=True
        )
        
        # Make stdout/stderr non-blocking on Unix
        if PLATFORM != "Windows":
            try:
                import fcntl
                if self.process.stdout:
                    fcntl.fcntl(self.process.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
                if self.process.stderr:
                    fcntl.fcntl(self.process.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            except Exception as e:
                logger.warning(f"Failed to set non-blocking I/O: {e}")
    
    def _io_worker(self) -> None:
        """I/O worker thread for handling input/output."""
        try:
            if self.use_pty:
                self._pty_io_worker()
            elif self.winpty_process:
                self._winpty_io_worker()
            else:
                self._pipe_io_worker()
        except Exception as e:
            logger.error(f"I/O worker error: {e}")
        finally:
            self.alive_event.clear()
    
    def _pty_io_worker(self) -> None:
        """I/O worker for PTY mode."""
        while self.alive_event.is_set():
            try:
                # Check if process is still alive
                if self.process and self.process.poll() is not None:
                    self.alive_event.clear()
                    break
                
                # Use select to check for available data
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                
                if ready and self.master_fd is not None:
                    try:
                        data = os.read(self.master_fd, 1024)
                        if data:
                            text = data.decode(self.encoding, errors='replace')
                            self.bytes_read += len(data)
                            self.output_queue.put(text)
                        else:
                            # EOF
                            self.alive_event.clear()
                            break
                    except OSError as e:
                        if e.errno in (11, 35):  # EAGAIN, EWOULDBLOCK
                            continue
                        else:
                            logger.debug(f"PTY read error: {e}")
                            self.alive_event.clear()
                            break
                
            except Exception as e:
                logger.debug(f"PTY I/O error: {e}")
                break
    
    def _winpty_io_worker(self) -> None:
        """I/O worker for winpty mode."""
        while self.alive_event.is_set():
            try:
                # Check if process is still alive
                if not self.winpty_process or not self.winpty_process.isalive():
                    self.alive_event.clear()
                    break
                
                # Read output
                try:
                    if self.winpty_process:
                        data = self.winpty_process.read(timeout=100)  # 100ms timeout
                        if data:
                            self.bytes_read += len(data.encode(self.encoding))
                            self.output_queue.put(data)
                except Exception:
                    # Timeout or no data available
                    continue
                
            except Exception as e:
                logger.debug(f"Winpty I/O error: {e}")
                break
    
    def _pipe_io_worker(self) -> None:
        """I/O worker for pipe mode."""
        while self.alive_event.is_set():
            try:
                # Check if process is still alive
                if self.process and self.process.poll() is not None:
                    # Read any remaining output
                    self._read_remaining_output()
                    self.alive_event.clear()
                    break
                
                # Read stdout
                if PLATFORM == "Windows":
                    # Windows doesn't support select on pipes
                    self._read_windows_output()
                else:
                    # Unix-like systems can use select
                    self._read_unix_output()
                
            except Exception as e:
                logger.debug(f"Pipe I/O error: {e}")
                break
    
    def _read_windows_output(self) -> None:
        """Read output on Windows (no select support)."""
        if not self.process:
            return
        
        # Use peek to check if data is available without blocking
        try:
            import msvcrt
            import sys
            
            # This is a simplified approach - in production you might want
            # to use threading for each pipe or polling
            if self.process.stdout:
                # Try to read with a very short timeout
                line = self.process.stdout.readline()
                if line:
                    self.bytes_read += len(line.encode(self.encoding))
                    self.output_queue.put(line)
            
            if self.process.stderr:
                line = self.process.stderr.readline()
                if line:
                    self.bytes_read += len(line.encode(self.encoding))
                    self.error_queue.put(line)
                    
        except Exception as e:
            logger.debug(f"Windows output read error: {e}")
    
    def _read_unix_output(self) -> None:
        """Read output on Unix-like systems."""
        if not self.process:
            return
        
        streams = []
        if self.process.stdout:
            streams.append(self.process.stdout)
        if self.process.stderr:
            streams.append(self.process.stderr)
        
        if not streams:
            time.sleep(0.1)
            return
        
        try:
            ready, _, _ = select.select(streams, [], [], 0.1)
            
            for stream in ready:
                try:
                    if stream == self.process.stdout:
                        data = stream.read(1024)
                        if data:
                            self.bytes_read += len(data.encode(self.encoding))
                            self.output_queue.put(data)
                    elif stream == self.process.stderr:
                        data = stream.read(1024)
                        if data:
                            self.bytes_read += len(data.encode(self.encoding))
                            self.error_queue.put(data)
                except Exception as e:
                    logger.debug(f"Stream read error: {e}")
                    
        except Exception as e:
            logger.debug(f"Select error: {e}")
    
    def _read_remaining_output(self) -> None:
        """Read any remaining output from terminated process."""
        if not self.process:
            return
        
        try:
            if self.process.stdout:
                remaining = self.process.stdout.read()
                if remaining:
                    self.bytes_read += len(remaining.encode(self.encoding))
                    self.output_queue.put(remaining)
            
            if self.process.stderr:
                remaining = self.process.stderr.read()
                if remaining:
                    self.bytes_read += len(remaining.encode(self.encoding))
                    self.error_queue.put(remaining)
                    
        except Exception as e:
            logger.debug(f"Error reading remaining output: {e}")
    
    def write(self, data: str) -> None:
        """
        Write data to process stdin.
        
        Args:
            data: Data to write
            
        Raises:
            CommandExecutionError: If process is not running or write fails
        """
        if not self.is_alive():
            raise CommandExecutionError("Process is not running")
        
        if not self.started_event.is_set():
            raise CommandExecutionError("Process has not started yet")
        
        try:
            if self.use_pty and self.master_fd is not None:
                # Write to PTY master
                encoded_data = data.encode(self.encoding)
                os.write(self.master_fd, encoded_data)
                self.bytes_written += len(encoded_data)
                
            elif self.winpty_process:
                # Write to winpty
                self.winpty_process.write(data)
                self.bytes_written += len(data.encode(self.encoding))
                
            elif self.process and self.process.stdin:
                # Write to pipe
                self.process.stdin.write(data)
                self.process.stdin.flush()
                self.bytes_written += len(data.encode(self.encoding))
                
            else:
                raise CommandExecutionError("No input stream available")
                
        except Exception as e:
            raise CommandExecutionError(f"Failed to write to process: {e}")
    
    def read_output(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Read output from process.
        
        Args:
            timeout: Timeout in seconds (None for non-blocking)
            
        Returns:
            Output string or None if no data available
        """
        try:
            if timeout is None:
                return self.output_queue.get_nowait()
            else:
                return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def read_error(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Read error output from process.
        
        Args:
            timeout: Timeout in seconds (None for non-blocking)
            
        Returns:
            Error string or None if no data available
        """
        try:
            if timeout is None:
                return self.error_queue.get_nowait()
            else:
                return self.error_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def read_lines(self, timeout: Optional[float] = 1.0) -> Generator[str, None, None]:
        """
        Generator that yields output lines.
        
        Args:
            timeout: Timeout for each read operation
            
        Yields:
            Output lines
        """
        buffer = ""
        
        while self.is_alive():
            try:
                data = self.read_output(timeout=timeout)
                if data:
                    buffer += data
                    
                    # Yield complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        yield line + '\n'
                else:
                    # No data available, check if process is still alive
                    if not self.is_alive():
                        break
                        
            except Exception as e:
                logger.debug(f"Error reading lines: {e}")
                break
        
        # Yield any remaining buffer content
        if buffer:
            yield buffer
    
    def send_signal(self, sig: int) -> None:
        """
        Send signal to process.
        
        Args:
            sig: Signal number
        """
        if not self.is_alive():
            return
        
        try:
            if PLATFORM == "Windows":
                if sig == signal.SIGINT:
                    # Send Ctrl+C to Windows process
                    if self.winpty_process:
                        # winpty handles signals differently
                        self.winpty_process.terminate()
                    elif self.process:
                        self.process.send_signal(signal.CTRL_C_EVENT)
                else:
                    if self.process:
                        self.process.terminate()
            else:
                # Unix-like systems
                if self.process:
                    try:
                        # Try to send signal to process group first
                        os.killpg(self.process.pid, sig)
                    except (OSError, ProcessLookupError):
                        # Fall back to sending signal to process only
                        self.process.send_signal(sig)
                        
        except Exception as e:
            logger.debug(f"Error sending signal {sig}: {e}")
    
    def terminate(self, grace_timeout: float = 5.0) -> bool:
        """
        Terminate the process gracefully.
        
        Args:
            grace_timeout: Time to wait for graceful termination
            
        Returns:
            True if terminated successfully
        """
        if not self.is_alive():
            return True
        
        logger.debug(f"Terminating interactive process PID {self.pid}")
        
        try:
            # Send SIGTERM (or equivalent)
            if PLATFORM == "Windows":
                if self.winpty_process:
                    self.winpty_process.terminate()
                elif self.process:
                    self.process.terminate()
            else:
                self.send_signal(signal.SIGTERM)
            
            # Wait for graceful termination
            start_time = time.time()
            while time.time() - start_time < grace_timeout:
                if not self.is_alive():
                    break
                time.sleep(0.1)
            
            # Force kill if still alive
            if self.is_alive():
                logger.debug(f"Force killing process PID {self.pid}")
                if self.winpty_process:
                    self.winpty_process.terminate(force=True)
                elif self.process:
                    if PLATFORM == "Windows":
                        self.process.kill()
                    else:
                        # Use process cleanup for thorough cleanup
                        cleanup_process_tree(self.process.pid)
            
            # Wait for I/O thread to finish
            self.alive_event.clear()
            if self.io_thread and self.io_thread.is_alive():
                self.io_thread.join(timeout=2.0)
            
            self._cleanup()
            self.end_time = time.time()
            
            return not self.is_alive()
            
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Close PTY file descriptors
            if self.master_fd is not None:
                os.close(self.master_fd)
                self.master_fd = None
                
            if self.slave_fd is not None:
                os.close(self.slave_fd)
                self.slave_fd = None
            
            # Close winpty
            if self.winpty_process:
                try:
                    self.winpty_process.terminate()
                except:
                    pass
                self.winpty_process = None
            
            # Close pipes
            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")
    
    def is_alive(self) -> bool:
        """Check if process is alive."""
        if self.winpty_process:
            return self.winpty_process.isalive()
        elif self.process:
            return self.process.poll() is None
        else:
            return False
    
    @property
    def pid(self) -> Optional[int]:
        """Get process PID."""
        if self.winpty_process:
            return self.winpty_process.pid
        elif self.process:
            return self.process.pid
        else:
            return None
    
    @property
    def exit_code(self) -> Optional[int]:
        """Get process exit code."""
        if self.winpty_process:
            return self.winpty_process.exitstatus if not self.winpty_process.isalive() else None
        elif self.process:
            return self.process.returncode
        else:
            return None
    
    @property
    def duration(self) -> Optional[float]:
        """Get process duration."""
        if self.start_time is None:
            return None
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get process statistics."""
        return {
            'pid': self.pid,
            'exit_code': self.exit_code,
            'duration': self.duration,
            'bytes_written': self.bytes_written,
            'bytes_read': self.bytes_read,
            'is_alive': self.is_alive(),
            'use_pty': self.use_pty,
            'platform': PLATFORM
        }
    
    def __enter__(self) -> 'InteractiveProcess':
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.terminate()
    
    def __del__(self) -> None:
        """Destructor - cleanup resources."""
        try:
            if self.is_alive():
                self.terminate(grace_timeout=1.0)
        except Exception:
            pass 