"""
Interactive session manager for handling multiple interactive command sessions.

This module provides a thread-safe singleton manager for handling multiple
interactive command sessions with support for both InteractiveProcess and
InteractivePexpectProcess backends, automatic cleanup and resource management.
"""

import threading
import time
import uuid
import atexit
import re
import platform
from typing import Dict, Optional, Any, List, Union, Type
from loguru import logger

from .interactive_executor import InteractiveCommandExecutor, InteractiveSession
from .interactive_process import InteractiveProcess
from .interactive_pexpect_process import InteractivePexpectProcess, PEXPECT_AVAILABLE
from .exceptions import CommandExecutionError


def clean_terminal_output(text: str) -> str:
    """
    Clean terminal control characters and ANSI escape sequences from output.
    
    Args:
        text: Raw terminal output
        
    Returns:
        Cleaned text with control characters removed
    """
    if not text:
        return text
    # return text
    
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Normalize Windows CRLF to LF first
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Handle standalone carriage returns (\r) that are used to return cursor to
    # the beginning of the line (common in interactive shells). We simulate the
    # overwrite by keeping only the content AFTER the last \r in each logical
    # line.
    if '\r' in text:
        processed_lines = []
        for raw_line in text.split('\n'):
            # Repeatedly process carriage returns within the line
            while '\r' in raw_line:
                raw_line = raw_line.split('\r')[-1]
            processed_lines.append(raw_line)
        text = '\n'.join(processed_lines)
    
    # Remove other control characters but keep newlines and tabs
    control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    text = control_chars.sub('', text)
    
    # Clean up multiple consecutive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


class ProcessType:
    """Constants for process types."""
    STANDARD = "standard"
    PEXPECT = "pexpect"


class ToolResult:
    """Result object for tool operations."""
    
    def __init__(self, success: bool, message: str, content: Optional[Union[Dict[str, Any], str]] = None):
        self.success = success
        self.message = message
        self.content = content or {}


class EnhancedSessionHandle:
    """Enhanced handle for managing an interactive session with process type support."""
    
    def __init__(
        self, 
        session: InteractiveSession, 
        command: str, 
        process_type: str,
        cwd: Optional[str] = None
    ):
        self.session = session
        self.command = command
        self.process_type = process_type
        self.cwd = cwd
        self.created_at = time.time()
        self.last_activity = time.time()
        
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            'session_id': self.session.session_id,
            'command': self.command,
            'process_type': self.process_type,
            'cwd': self.cwd,
            'pid': self.session.process.pid if self.session.process else None,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'duration': time.time() - self.created_at,
            'idle_time': time.time() - self.last_activity,
            'is_alive': self.session.process.is_alive() if self.session.process else False
        }


class InteractiveSessionManager:
    """Thread-safe singleton manager for interactive command sessions with process type switching."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.sessions: Dict[str, EnhancedSessionHandle] = {}
        self.executor = InteractiveCommandExecutor(verbose=False)
        self._cleanup_lock = threading.Lock()
        self._cleanup_thread = None
        self._shutdown = False
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("InteractiveSessionManager initialized with process type switching support")
    
    def _start_cleanup_thread(self):
        """Start the background cleanup thread."""
        def cleanup_worker():
            while not self._shutdown:
                try:
                    self._cleanup_idle_sessions()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_idle_sessions(self):
        """Clean up idle sessions (30 minutes of inactivity)."""
        current_time = time.time()
        idle_timeout = 30 * 60  # 30 minutes
        
        with self._cleanup_lock:
            to_remove = []
            for session_id, handle in self.sessions.items():
                if current_time - handle.last_activity > idle_timeout:
                    logger.info(f"Cleaning up idle session {session_id} (type: {handle.process_type})")
                    try:
                        handle.session.terminate()
                    except Exception as e:
                        logger.error(f"Error terminating idle session {session_id}: {e}")
                    to_remove.append(session_id)
            
            for session_id in to_remove:
                self.sessions.pop(session_id, None)
    
    def _determine_process_type(
        self, 
        command: str, 
        use_pexpect: Optional[bool] = None
    ) -> str:
        """
        Determine the best process type for a command.
        
        Args:
            command: Command to execute
            use_pexpect: Explicit process type selection
            
        Returns:
            Process type string
        """
        # Explicit selection
        if use_pexpect is not None:
            if use_pexpect:
                if PEXPECT_AVAILABLE:
                    return ProcessType.PEXPECT
                else:
                    logger.warning("pexpect requested but not available, falling back to standard process")
                    return ProcessType.STANDARD
            else:
                return ProcessType.STANDARD
        
        # Automatic selection based on command and platform
        if not PEXPECT_AVAILABLE:
            return ProcessType.STANDARD
        
        # Commands that benefit from pexpect
        interactive_commands = [
            'python', 'python3', 'node', 'repl', 'irb', 'ghci',
            'mysql', 'psql', 'sqlite3', 'redis-cli', 'mongo',
            'ssh', 'telnet', 'ftp', 'sftp'
        ]
        
        cmd_lower = command.lower()
        for interactive_cmd in interactive_commands:
            if cmd_lower.startswith(interactive_cmd):
                logger.debug(f"Auto-selecting pexpect for interactive command: {command}")
                return ProcessType.PEXPECT
        
        # Default to standard process
        return ProcessType.STANDARD
    
    def _create_process(
        self, 
        command: str, 
        process_type: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Union[InteractiveProcess, InteractivePexpectProcess]:
        """
        Create a process of the specified type.
        
        Args:
            command: Command to execute
            process_type: Type of process to create
            cwd: Working directory
            env: Environment variables
            timeout: Process timeout
            **kwargs: Additional process arguments
            
        Returns:
            Process instance
            
        Raises:
            CommandExecutionError: If process creation fails
        """
        try:
            if process_type == ProcessType.PEXPECT:
                if not PEXPECT_AVAILABLE:
                    raise CommandExecutionError("pexpect not available on this platform")
                
                process = InteractivePexpectProcess(
                    command=command,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                    **kwargs
                )
            else:
                process = InteractiveProcess(
                    command=command,
                    cwd=cwd,
                    env=env,
                    **kwargs
                )
            
            process.start()
            return process
            
        except Exception as e:
            # Fallback to standard process if pexpect fails
            if process_type == ProcessType.PEXPECT:
                logger.warning(f"pexpect process creation failed, falling back to standard: {e}")
                return self._create_process(
                    command, ProcessType.STANDARD, cwd, env, timeout, **kwargs
                )
            else:
                raise CommandExecutionError(f"Failed to create process: {e}")
    
    def create_session(
        self, 
        command: str, 
        cwd: Optional[str] = None, 
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        use_pexpect: Optional[bool] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Create a new interactive session with automatic or manual process type selection.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Session timeout in seconds
            use_pexpect: Explicit process type selection (None=auto, True=pexpect, False=standard)
            session_id: Custom session ID
            **kwargs: Additional process arguments
            
        Returns:
            ToolResult with session information
        """
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Determine process type
            process_type = self._determine_process_type(command, use_pexpect)
            
            # Create process
            process = self._create_process(
                command=command,
                process_type=process_type,
                cwd=cwd,
                env=env,
                timeout=timeout,
                **kwargs
            )
            
            # Create session wrapper
            session = InteractiveSession(
                process=process,
                session_id=session_id,
                timeout=timeout
            )
            
            # Create enhanced handle
            handle = EnhancedSessionHandle(session, command, process_type, cwd)
            
            # Store session
            with self._cleanup_lock:
                self.sessions[session_id] = handle
            
            logger.info(f"Created interactive session {session_id} using {process_type} process for command: {command}")
            
            return ToolResult(
                success=True,
                message=f"Interactive session started successfully using {process_type} process",
                content={
                    'session_id': session_id,
                    'pid': process.pid if process else None,
                    'command': command,
                    'process_type': process_type,
                    'cwd': cwd,
                    'created_at': handle.created_at
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create interactive session: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to create interactive session: {str(e)}"
            )
    
    def send_input(
        self, 
        session_id: str, 
        input_text: str, 
        read_timeout: Optional[int] = None,
        max_bytes: Optional[int] = None,
        expect_prompt: Optional[bool] = False,
        prompt_regex: Optional[str] = r'>>> ?$'
    ) -> ToolResult:
        """
        Send input to a session and read output with process-type-aware handling.
        
        Args:
            session_id: Session ID
            input_text: Text to send to stdin
            read_timeout: Timeout for reading output
            max_bytes: Maximum bytes to read
            expect_prompt: Whether to wait for prompt before returning
            prompt_regex: Regular expression to match prompt
            
        Returns:
            ToolResult with output
        """
        with self._cleanup_lock:
            handle = self.sessions.get(session_id)
            if not handle:
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} not found"
                )
            
            # Update activity
            handle.update_activity()
        
        try:
            # Check if session is still alive
            if not handle.session.process.is_alive():
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} is no longer alive"
                )
            
            # Send input based on process type
            if handle.process_type == ProcessType.PEXPECT:
                # Use pexpect-specific methods
                if hasattr(handle.session.process, 'sendline'):
                    # Remove trailing newline if present since sendline adds it
                    clean_input = input_text.rstrip('\n\r')
                    handle.session.process.sendline(clean_input)
                else:
                    handle.session.process.write(input_text)
            else:
                # Use standard process write
                handle.session.process.write(input_text)
            
            # Read output based on expect_prompt setting and process type
            if expect_prompt and handle.process_type == ProcessType.PEXPECT:
                # Use pexpect expect functionality
                raw_output = self._read_until_prompt_pexpect(
                    handle.session.process, 
                    prompt_regex or r'>>> ?$',
                    read_timeout or 2
                )
            elif expect_prompt:
                # Use standard process with prompt detection
                raw_output = self._read_until_prompt(
                    handle.session.process, 
                    prompt_regex or r'>>> ?$',
                    read_timeout or 2
                )
            else:
                # Standard output reading
                raw_output = handle.session.process.read_output(
                    timeout=read_timeout or 2
                )
            
            # Clean the output to remove terminal control characters
            cleaned_output = clean_terminal_output(raw_output or '')
            
            logger.debug(f"Session {session_id} ({handle.process_type}): sent input, got {len(raw_output or '')} bytes raw output, {len(cleaned_output)} chars cleaned, expect_prompt={expect_prompt}")
            
            return ToolResult(
                success=True,
                message="Input sent and output received",
                content={
                    'session_id': session_id,
                    'output': cleaned_output,
                    'raw_output': raw_output or '',
                    'input_sent': input_text,
                    'bytes_read': len(raw_output or ''),
                    'cleaned_length': len(cleaned_output),
                    'process_type': handle.process_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error interacting with session {session_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Error interacting with session: {str(e)}"
            )

    def read_output(
        self, 
        session_id: str, 
        read_timeout: Optional[int] = None,
        max_bytes: Optional[int] = None,
        expect_prompt: Optional[bool] = False,
        prompt_regex: Optional[str] = r'>>> ?$'
    ) -> ToolResult:
        """
        Read output from a session without sending any input.
        
        Args:
            session_id: Session ID
            read_timeout: Timeout for reading output
            max_bytes: Maximum bytes to read
            expect_prompt: Whether to wait for prompt before returning
            prompt_regex: Regular expression to match prompt
            
        Returns:
            ToolResult with output
        """
        with self._cleanup_lock:
            handle = self.sessions.get(session_id)
            if not handle:
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} not found"
                )
            
            # Update activity
            handle.update_activity()
        
        try:
            # Check if session is still alive
            if not handle.session.process.is_alive():
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} is no longer alive"
                )
            
            # Read output based on process type and expect_prompt setting
            if expect_prompt and handle.process_type == ProcessType.PEXPECT:
                raw_output = self._read_until_prompt_pexpect(
                    handle.session.process, 
                    prompt_regex or r'>>> ?$',
                    read_timeout or 2
                )
            elif expect_prompt:
                raw_output = self._read_until_prompt(
                    handle.session.process, 
                    prompt_regex or r'>>> ?$',
                    read_timeout or 2
                )
            else:
                raw_output = handle.session.process.read_output(
                    timeout=read_timeout or 2
                )
            
            # Clean the output to remove terminal control characters
            cleaned_output = clean_terminal_output(raw_output or '')
            
            logger.debug(f"Session {session_id} ({handle.process_type}): read output only, got {len(raw_output or '')} bytes raw output, {len(cleaned_output)} chars cleaned, expect_prompt={expect_prompt}")
            
            return ToolResult(
                success=True,
                message="Output read successfully",
                content={
                    'session_id': session_id,
                    'output': cleaned_output,
                    'raw_output': raw_output or '',
                    'input_sent': None,
                    'bytes_read': len(raw_output or ''),
                    'cleaned_length': len(cleaned_output),
                    'process_type': handle.process_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error reading output from session {session_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Error reading output from session: {str(e)}"
            )

    def read_output_progressive(
        self, 
        session_id: str, 
        read_timeout: Optional[int] = None,
        max_bytes: Optional[int] = None,
        expect_prompt: Optional[bool] = False,
        prompt_regex: Optional[str] = r'>>> ?$'
    ) -> ToolResult:
        """
        Progressively read output from a session with intelligent timeout handling.
        
        This method waits for initial output, then continues reading as long as content
        is available, stopping only after 5 seconds of no new content.
        
        Args:
            session_id: Session ID
            read_timeout: Initial timeout for reading output (default: 3 seconds)
            max_bytes: Maximum bytes to read in total
            expect_prompt: Whether to wait for prompt before returning
            prompt_regex: Regular expression to match prompt
            
        Returns:
            ToolResult with accumulated output
        """
        with self._cleanup_lock:
            handle = self.sessions.get(session_id)
            if not handle:
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} not found"
                )
            
            # Update activity
            handle.update_activity()
        
        try:
            # Check if session is still alive
            if not handle.session.process.is_alive():
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} is no longer alive"
                )
            
            # Progressive reading logic
            initial_timeout = read_timeout or 3
            accumulated_output = ""
            total_bytes_read = 0
            read_cycles = 0
            no_content_duration = 0
            last_read_time = time.time()
            
            logger.debug(f"Session {session_id} ({handle.process_type}): Starting progressive read with initial timeout {initial_timeout}s")
            
            while True:
                read_cycles += 1
                cycle_start_time = time.time()
                
                # Read with current timeout
                if expect_prompt and accumulated_output:
                    # If we already have some output and expect prompt, check if we found it
                    lines = accumulated_output.split('\n')
                    if lines and re.search(prompt_regex or r'>>> ?$', lines[-1]):
                        logger.debug(f"Session {session_id}: Found prompt pattern, stopping progressive read")
                        break
                
                # Read a chunk
                chunk = handle.session.process.read_output(timeout=initial_timeout)
                
                if chunk and chunk.strip():
                    # Got content, reset no-content counter
                    accumulated_output += chunk
                    total_bytes_read += len(chunk)
                    no_content_duration = 0
                    last_read_time = time.time()
                    
                    logger.debug(f"Session {session_id}: Read cycle {read_cycles}, got {len(chunk)} bytes, total: {total_bytes_read} bytes")
                    
                    # Check max_bytes limit
                    if max_bytes and total_bytes_read >= max_bytes:
                        logger.debug(f"Session {session_id}: Reached max_bytes limit ({max_bytes}), stopping")
                        break
                        
                else:
                    # No content in this cycle
                    current_time = time.time()
                    no_content_duration += current_time - cycle_start_time
                    
                    logger.debug(f"Session {session_id}: Read cycle {read_cycles}, no content for {no_content_duration:.1f}s")
                    
                    # If we have some content and no new content for 5 seconds, stop
                    if accumulated_output and no_content_duration >= 5.0:
                        logger.debug(f"Session {session_id}: No new content for 5 seconds, stopping progressive read")
                        break
                    
                    # If we have no content at all and waited initial timeout, stop
                    if not accumulated_output and no_content_duration >= initial_timeout:
                        logger.debug(f"Session {session_id}: No initial content after {initial_timeout}s, stopping")
                        break
                
                # Brief pause between cycles to avoid excessive CPU usage
                time.sleep(0.1)
            
            # Clean the accumulated output
            cleaned_output = clean_terminal_output(accumulated_output)
            
            logger.debug(f"Session {session_id} ({handle.process_type}): Progressive read completed after {read_cycles} cycles, "
                        f"got {total_bytes_read} bytes raw output, {len(cleaned_output)} chars cleaned")
            
            return ToolResult(
                success=True,
                message=f"Progressive output read completed ({read_cycles} cycles)",
                content={
                    'session_id': session_id,
                    'output': cleaned_output,
                    'raw_output': accumulated_output,
                    'input_sent': None,
                    'bytes_read': total_bytes_read,
                    'cleaned_length': len(cleaned_output),
                    'read_cycles': read_cycles,
                    'total_duration': time.time() - last_read_time + no_content_duration,
                    'process_type': handle.process_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in progressive read from session {session_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Error in progressive read from session: {str(e)}"
            )

    def send_input_then_get_progressive(
        self, 
        session_id: str, 
        input_text: str,
        read_timeout: Optional[int] = None,
        max_bytes: Optional[int] = None,
        expect_prompt: Optional[bool] = False,
        prompt_regex: Optional[str] = r'>>> ?$'
    ) -> ToolResult:
        """
        Send input to a session and then progressively read output with intelligent timeout handling.
        
        This method sends input first, then waits for initial output and continues reading 
        as long as content is available, stopping only after 5 seconds of no new content.
        
        Args:
            session_id: Session ID
            input_text: Text to send to stdin
            read_timeout: Initial timeout for reading output (default: 3 seconds)
            max_bytes: Maximum bytes to read in total
            expect_prompt: Whether to wait for prompt before returning
            prompt_regex: Regular expression to match prompt
            
        Returns:
            ToolResult with accumulated output
        """
        with self._cleanup_lock:
            handle = self.sessions.get(session_id)
            if not handle:
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} not found"
                )
            
            # Update activity
            handle.update_activity()
        
        try:
            # Check if session is still alive
            if not handle.session.process.is_alive():
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} is no longer alive"
                )
            
            # Send input first
            logger.debug(f"Session {session_id} ({handle.process_type}): Sending input: {input_text[:50]}...")
            
            if handle.process_type == ProcessType.PEXPECT:
                # Use pexpect-specific methods
                if hasattr(handle.session.process, 'sendline'):
                    clean_input = input_text.rstrip('\n\r')
                    handle.session.process.sendline(clean_input)
                else:
                    handle.session.process.write(input_text)
            else:
                handle.session.process.write(input_text)
            
            # Progressive reading logic (similar to read_output_progressive)
            initial_timeout = read_timeout or 3
            accumulated_output = ""
            total_bytes_read = 0
            read_cycles = 0
            no_content_duration = 0
            last_read_time = time.time()
            
            logger.debug(f"Session {session_id} ({handle.process_type}): Starting progressive read after input with initial timeout {initial_timeout}s")
            
            while True:
                read_cycles += 1
                cycle_start_time = time.time()
                
                # Read with current timeout
                if expect_prompt and accumulated_output:
                    # If we already have some output and expect prompt, check if we found it
                    lines = accumulated_output.split('\n')
                    if lines and re.search(prompt_regex or r'>>> ?$', lines[-1]):
                        logger.debug(f"Session {session_id}: Found prompt pattern, stopping progressive read")
                        break
                
                # Read a chunk
                chunk = handle.session.process.read_output(timeout=initial_timeout)
                
                if chunk and chunk.strip():
                    # Got content, reset no-content counter
                    accumulated_output += chunk
                    total_bytes_read += len(chunk)
                    no_content_duration = 0
                    last_read_time = time.time()
                    
                    logger.debug(f"Session {session_id}: Read cycle {read_cycles}, got {len(chunk)} bytes, total: {total_bytes_read} bytes")
                    
                    # Check max_bytes limit
                    if max_bytes and total_bytes_read >= max_bytes:
                        logger.debug(f"Session {session_id}: Reached max_bytes limit ({max_bytes}), stopping")
                        break
                        
                else:
                    # No content in this cycle
                    current_time = time.time()
                    no_content_duration += current_time - cycle_start_time
                    
                    logger.debug(f"Session {session_id}: Read cycle {read_cycles}, no content for {no_content_duration:.1f}s")
                    
                    # If we have some content and no new content for 5 seconds, stop
                    if accumulated_output and no_content_duration >= 5.0:
                        logger.debug(f"Session {session_id}: No new content for 5 seconds, stopping progressive read")
                        break
                    
                    # If we have no content at all and waited initial timeout, stop
                    if not accumulated_output and no_content_duration >= initial_timeout:
                        logger.debug(f"Session {session_id}: No initial content after {initial_timeout}s, stopping")
                        break
                
                # Brief pause between cycles to avoid excessive CPU usage
                time.sleep(0.1)
            
            # Clean the accumulated output
            cleaned_output = clean_terminal_output(accumulated_output)
            
            logger.debug(f"Session {session_id} ({handle.process_type}): Progressive read after input completed after {read_cycles} cycles, "
                        f"got {total_bytes_read} bytes raw output, {len(cleaned_output)} chars cleaned")
            
            return ToolResult(
                success=True,
                message=f"Input sent and progressive output read completed ({read_cycles} cycles)",
                content={
                    'session_id': session_id,
                    'output': cleaned_output,
                    'raw_output': accumulated_output,
                    'input_sent': input_text,
                    'bytes_read': total_bytes_read,
                    'cleaned_length': len(cleaned_output),
                    'read_cycles': read_cycles,
                    'total_duration': time.time() - last_read_time + no_content_duration,
                    'process_type': handle.process_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in send input then progressive read from session {session_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Error in send input then progressive read from session: {str(e)}"
            )
    
    def terminate_session(self, session_id: str, force: bool = False) -> ToolResult:
        """
        Terminate a session.
        
        Args:
            session_id: Session ID
            force: Whether to force termination
            
        Returns:
            ToolResult indicating success
        """
        with self._cleanup_lock:
            handle = self.sessions.pop(session_id, None)
            if not handle:
                return ToolResult(
                    success=False,
                    message=f"Session {session_id} not found"
                )
        
        try:
            if force:
                # Force termination - use terminate with grace_timeout=0
                handle.session.process.terminate(grace_timeout=0.0)
            else:
                # Graceful termination
                handle.session.terminate()
            
            logger.info(f"Terminated session {session_id} ({handle.process_type}, force={force})")
            
            return ToolResult(
                success=True,
                message=f"Session {session_id} terminated successfully",
                content={
                    'session_id': session_id,
                    'process_type': handle.process_type,
                    'terminated': True,
                    'force': force
                }
            )
            
        except Exception as e:
            logger.error(f"Error terminating session {session_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Error terminating session: {str(e)}"
            )
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        with self._cleanup_lock:
            handle = self.sessions.get(session_id)
            if handle:
                return handle.get_stats()
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions with process type information."""
        with self._cleanup_lock:
            return [handle.get_stats() for handle in self.sessions.values()]
    
    def get_process_type_stats(self) -> Dict[str, Any]:
        """Get statistics about process types in use."""
        with self._cleanup_lock:
            stats = {
                'total_sessions': len(self.sessions),
                'by_process_type': {},
                'pexpect_available': PEXPECT_AVAILABLE,
                'platform': platform.system()
            }
            
            for handle in self.sessions.values():
                process_type = handle.process_type
                if process_type not in stats['by_process_type']:
                    stats['by_process_type'][process_type] = 0
                stats['by_process_type'][process_type] += 1
            
            return stats
    
    def cleanup_all(self):
        """Clean up all sessions."""
        self._shutdown = True
        
        with self._cleanup_lock:
            for session_id, handle in list(self.sessions.items()):
                try:
                    logger.info(f"Cleaning up session {session_id} ({handle.process_type})")
                    handle.session.terminate()
                except Exception as e:
                    logger.error(f"Error terminating session {session_id} during cleanup: {e}")
            
            self.sessions.clear()
        
        # Clean up executor
        try:
            self.executor.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up executor: {e}")
        
        logger.info("InteractiveSessionManager cleanup completed")
    
    def _read_until_prompt(self, process, prompt_regex: str, timeout: int) -> str:
        """
        Read output until a prompt pattern is found or timeout occurs (standard process).
        
        Args:
            process: The interactive process
            prompt_regex: Regular expression to match prompt
            timeout: Total timeout in seconds
            
        Returns:
            Accumulated output string
        """
        import time
        import re
        
        start_time = time.time()
        accumulated_output = ""
        prompt_pattern = re.compile(prompt_regex, re.MULTILINE)
        
        while time.time() - start_time < timeout:
            # Read a chunk with short timeout
            chunk = process.read_output(timeout=0.1)
            if chunk:
                accumulated_output += chunk
                
                # Check if we found the prompt pattern
                # Look for prompt at the end of the accumulated output
                lines = accumulated_output.split('\n')
                if len(lines) > 0:
                    last_line = lines[-1]
                    if prompt_pattern.search(last_line):
                        logger.debug(f"Found prompt pattern '{prompt_regex}' in: {repr(last_line)}")
                        break
            else:
                # No output available, sleep briefly
                time.sleep(0.05)
        
        return accumulated_output
    
    def _read_until_prompt_pexpect(self, process, prompt_regex: str, timeout: int) -> str:
        """
        Read output until a prompt pattern is found using pexpect expect functionality.
        
        Args:
            process: The pexpect process
            prompt_regex: Regular expression to match prompt
            timeout: Total timeout in seconds
            
        Returns:
            Accumulated output string
        """
        try:
            if hasattr(process, 'expect'):
                # Use pexpect's built-in expect functionality
                process.expect(prompt_regex, timeout=timeout)
                # Return the output before the match
                before = getattr(process, 'before', '')
                after = getattr(process, 'after', '')
                return (before or '') + (after or '')
            else:
                # Fallback to standard prompt reading
                return self._read_until_prompt(process, prompt_regex, timeout)
        except Exception as e:
            logger.debug(f"pexpect expect failed, using fallback: {e}")
            return self._read_until_prompt(process, prompt_regex, timeout)


# Global instance
_session_manager = None
_session_manager_lock = threading.Lock()


def get_session_manager() -> InteractiveSessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        with _session_manager_lock:
            if _session_manager is None:
                _session_manager = InteractiveSessionManager()
    return _session_manager 