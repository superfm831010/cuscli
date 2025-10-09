"""
Interactive process wrapper using pexpect for shell command execution.

This module provides pexpect-based interactive process functionality including:
- Real-time input/output streaming with pexpect
- Cross-platform support (Unix-like systems)
- Signal handling (Ctrl-C, etc.)
- Thread-safe operations
- Pattern matching and expect functionality
"""

import os
import platform
import threading
import time
import queue
import signal
from typing import Optional, Dict, Any, Generator, Union, List, Tuple
from loguru import logger

from .exceptions import CommandExecutionError, ProcessCleanupError
from .process_cleanup import cleanup_process_tree

# Platform check
PLATFORM = platform.system()
PEXPECT_AVAILABLE = False

try:
    import pexpect
    if PLATFORM != "Windows":
        PEXPECT_AVAILABLE = True
    else:
        # Try to import pexpect for Windows (pexpect-windows)
        try:
            import pexpect.popen_spawn
            PEXPECT_AVAILABLE = True
        except ImportError:
            logger.debug("pexpect not fully available on Windows")
except ImportError:
    logger.debug("pexpect not available")


class InteractivePexpectProcess:
    """
    Interactive process wrapper using pexpect for real-time command execution.
    
    This class provides a pexpect-based interface for executing commands that
    require interactive input/output, with built-in pattern matching and
    expect functionality.
    """
    
    def __init__(
        self,
        command: Union[str, List[str]],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        encoding: str = 'utf-8',
        timeout: Optional[float] = None,
        maxread: int = 2000,
        searchwindowsize: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize interactive pexpect process.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            encoding: Text encoding
            timeout: Default timeout for expect operations
            maxread: Maximum bytes to read at once
            searchwindowsize: Size of search window for pattern matching
            **kwargs: Additional pexpect arguments
        """
        self.command = command
        self.cwd = cwd
        self.env = env
        self.encoding = encoding
        self.shell = shell
        self.timeout = timeout
        self.maxread = maxread
        self.searchwindowsize = searchwindowsize
        self.pexpect_kwargs = kwargs
        
        # Check availability
        if not PEXPECT_AVAILABLE:
            raise CommandExecutionError("pexpect not available on this platform")
        
        # State management
        self.child: Optional[pexpect.spawn] = None
        self.logfile_read = None
        self.logfile_send = None
        
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
        
        # Buffer for continuous reading
        self._output_buffer = ""
        self._read_lock = threading.Lock()
        
        logger.debug(f"InteractivePexpectProcess initialized: platform={PLATFORM}")
    
    def start(self) -> None:
        """Start the interactive pexpect process."""
        if self.is_alive():
            raise CommandExecutionError("Process is already running")
        
        self.start_time = time.time()
        self.alive_event.set()
        
        try:
            # Prepare command
            if isinstance(self.command, list):
                if self.shell:
                    # Join command parts for shell execution
                    cmd = ' '.join(self.command)
                else:
                    # Use first element as command, rest as args
                    cmd = self.command[0]
                    args = self.command[1:] if len(self.command) > 1 else []
            else:
                cmd = self.command
                args = []
            
            # Create pexpect spawn
            if PLATFORM == "Windows":
                # Use popen_spawn for Windows
                self.child = pexpect.popen_spawn.PopenSpawn(
                    cmd,
                    timeout=self.timeout,
                    maxread=self.maxread,
                    searchwindowsize=self.searchwindowsize,
                    encoding=self.encoding,
                    cwd=self.cwd,
                    env=self.env,
                    **self.pexpect_kwargs
                )
            else:
                # Use regular spawn for Unix-like systems
                if self.shell:
                    # Use shell to execute command
                    shell_cmd = os.environ.get("SHELL", "/bin/sh")
                    self.child = pexpect.spawn(
                        shell_cmd,
                        args=["-c", cmd],
                        timeout=self.timeout,
                        maxread=self.maxread,
                        searchwindowsize=self.searchwindowsize,
                        encoding=self.encoding,
                        cwd=self.cwd,
                        env=self.env,
                        **self.pexpect_kwargs
                    )
                else:
                    # Direct command execution
                    self.child = pexpect.spawn(
                        cmd,
                        args=args,
                        timeout=self.timeout,
                        maxread=self.maxread,
                        searchwindowsize=self.searchwindowsize,
                        encoding=self.encoding,
                        cwd=self.cwd,
                        env=self.env,
                        **self.pexpect_kwargs
                    )
            
            # Configure logging if needed
            if hasattr(self, 'logfile_read') and self.logfile_read:
                self.child.logfile_read = self.logfile_read
            if hasattr(self, 'logfile_send') and self.logfile_send:
                self.child.logfile_send = self.logfile_send
            
            # Start I/O thread for continuous reading
            self.io_thread = threading.Thread(target=self._io_worker, daemon=True)
            self.io_thread.start()
            
            # Give process a moment to start
            time.sleep(0.1)
            
            # Check if process is alive
            if not self.is_alive():
                self._cleanup()
                raise CommandExecutionError("Pexpect process failed to start")
            
            self.started_event.set()
            logger.info(f"Interactive pexpect process started: PID {self.pid}")
            
        except Exception as e:
            self.alive_event.clear()
            self._cleanup()
            raise CommandExecutionError(f"Failed to start pexpect process: {e}")
    
    def _io_worker(self) -> None:
        """I/O worker thread for continuous reading."""
        try:
            while self.alive_event.is_set() and self.child and self.child.isalive():
                try:
                    # Read data with timeout
                    data = self.child.read_nonblocking(size=1024, timeout=0.1)
                    if data:
                        with self._read_lock:
                            self._output_buffer += data
                            self.bytes_read += len(data.encode(self.encoding))
                            self.output_queue.put(data)
                    
                except pexpect.TIMEOUT:
                    # No data available, continue
                    continue
                except pexpect.EOF:
                    # Process terminated
                    self.alive_event.clear()
                    break
                except Exception as e:
                    logger.debug(f"I/O worker error: {e}")
                    break
            
        except Exception as e:
            logger.error(f"I/O worker fatal error: {e}")
        finally:
            self.alive_event.clear()
    
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
            if self.child:
                self.child.send(data)
                self.bytes_written += len(data.encode(self.encoding))
            else:
                raise CommandExecutionError("No pexpect child process available")
                
        except Exception as e:
            raise CommandExecutionError(f"Failed to write to process: {e}")
    
    def sendline(self, line: str = "") -> None:
        """
        Send a line to the process (adds newline).
        
        Args:
            line: Line to send
        """
        if self.child:
            self.child.sendline(line)
            self.bytes_written += len(line.encode(self.encoding)) + 1  # +1 for newline
    
    def sendcontrol(self, char: str) -> None:
        """
        Send a control character to the process.
        
        Args:
            char: Control character (e.g., 'c' for Ctrl-C)
        """
        if self.child:
            self.child.sendcontrol(char)
            self.bytes_written += 1
    
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
    
    def expect(self, pattern: Union[str, List[str]], timeout: Optional[float] = None) -> int:
        """
        Wait for a pattern to appear in the output.
        
        Args:
            pattern: Pattern(s) to match
            timeout: Timeout in seconds
            
        Returns:
            Index of matched pattern (0 if single pattern)
            
        Raises:
            CommandExecutionError: If expect fails
        """
        if not self.child:
            raise CommandExecutionError("No pexpect child process available")
        
        try:
            if timeout is None:
                timeout = self.timeout
            
            result = self.child.expect(pattern, timeout=timeout)
            
            # Add matched text to output queue
            if self.child.after:
                self.output_queue.put(self.child.after)
            
            return result
            
        except pexpect.TIMEOUT as e:
            raise CommandExecutionError(f"Expect timeout: {e}")
        except pexpect.EOF as e:
            raise CommandExecutionError(f"Expect EOF: {e}")
        except Exception as e:
            raise CommandExecutionError(f"Expect error: {e}")
    
    def expect_exact(self, pattern: Union[str, List[str]], timeout: Optional[float] = None) -> int:
        """
        Wait for exact string(s) to appear in the output.
        
        Args:
            pattern: Exact string(s) to match
            timeout: Timeout in seconds
            
        Returns:
            Index of matched pattern (0 if single pattern)
        """
        if not self.child:
            raise CommandExecutionError("No pexpect child process available")
        
        try:
            if timeout is None:
                timeout = self.timeout
            
            result = self.child.expect_exact(pattern, timeout=timeout)
            
            # Add matched text to output queue
            if self.child.after:
                self.output_queue.put(self.child.after)
            
            return result
            
        except pexpect.TIMEOUT as e:
            raise CommandExecutionError(f"Expect exact timeout: {e}")
        except pexpect.EOF as e:
            raise CommandExecutionError(f"Expect exact EOF: {e}")
        except Exception as e:
            raise CommandExecutionError(f"Expect exact error: {e}")
    
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
    
    def interact(self, escape_character: str = chr(29), input_filter=None, output_filter=None) -> None:
        """
        Give control of the child process to the user.
        
        Args:
            escape_character: Character to exit interaction
            input_filter: Filter for input
            output_filter: Filter for output
        """
        if not self.child:
            raise CommandExecutionError("No pexpect child process available")
        
        try:
            self.child.interact(
                escape_character=escape_character,
                input_filter=input_filter,
                output_filter=output_filter
            )
        except Exception as e:
            raise CommandExecutionError(f"Interaction error: {e}")
    
    def send_signal(self, sig: int) -> None:
        """
        Send signal to process.
        
        Args:
            sig: Signal number
        """
        if not self.is_alive():
            return
        
        try:
            if self.child:
                if PLATFORM == "Windows":
                    # Windows signal handling
                    if sig == signal.SIGINT:
                        self.child.sendcontrol('c')
                    else:
                        self.child.terminate()
                else:
                    # Unix signal handling
                    self.child.kill(sig)
                    
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
        
        logger.debug(f"Terminating pexpect process PID {self.pid}")
        
        try:
            # Send SIGTERM (or equivalent)
            if self.child:
                self.child.terminate()
            
            # Wait for graceful termination
            start_time = time.time()
            while time.time() - start_time < grace_timeout:
                if not self.is_alive():
                    break
                time.sleep(0.1)
            
            # Force kill if still alive
            if self.is_alive() and self.child:
                logger.debug(f"Force killing pexpect process PID {self.pid}")
                self.child.kill(signal.SIGKILL)
            
            # Wait for I/O thread to finish
            self.alive_event.clear()
            if self.io_thread and self.io_thread.is_alive():
                self.io_thread.join(timeout=2.0)
            
            self._cleanup()
            self.end_time = time.time()
            
            return not self.is_alive()
            
        except Exception as e:
            logger.error(f"Error terminating pexpect process: {e}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.child:
                try:
                    if self.child.isalive():
                        self.child.terminate(force=True)
                except:
                    pass
                
                # Close file descriptors
                try:
                    self.child.close()
                except:
                    pass
                
                self.child = None
                    
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")
    
    def is_alive(self) -> bool:
        """Check if process is alive."""
        if self.child:
            return self.child.isalive()
        return False
    
    @property
    def pid(self) -> Optional[int]:
        """Get process PID."""
        if self.child:
            return self.child.pid
        return None
    
    @property
    def exit_code(self) -> Optional[int]:
        """Get process exit code."""
        if self.child:
            return self.child.exitstatus
        return None
    
    @property
    def signal_status(self) -> Optional[int]:
        """Get process signal status."""
        if self.child:
            return self.child.signalstatus
        return None
    
    @property
    def duration(self) -> Optional[float]:
        """Get process duration."""
        if self.start_time is None:
            return None
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    @property
    def before(self) -> Optional[str]:
        """Get text before the last match."""
        if self.child:
            return self.child.before
        return None
    
    @property
    def after(self) -> Optional[str]:
        """Get text after the last match."""
        if self.child:
            return self.child.after
        return None
    
    @property
    def match(self) -> Optional[str]:
        """Get the last match object."""
        if self.child:
            return self.child.match
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get process statistics."""
        return {
            'pid': self.pid,
            'exit_code': self.exit_code,
            'signal_status': self.signal_status,
            'duration': self.duration,
            'bytes_written': self.bytes_written,
            'bytes_read': self.bytes_read,
            'is_alive': self.is_alive(),
            'platform': PLATFORM,
            'pexpect_available': PEXPECT_AVAILABLE
        }
    
    def __enter__(self) -> 'InteractivePexpectProcess':
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