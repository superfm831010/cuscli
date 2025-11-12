"""
Process cleanup module for shell command execution.

This module provides comprehensive process cleanup functionality including:
- Cross-platform process tree cleanup
- Graceful and forced termination
- Zombie process prevention
- Process group management
"""

import os
import signal
import platform
import time
from typing import List, Optional
from loguru import logger

from .exceptions import ProcessCleanupError, ProcessNotFoundError

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    logger.warning("psutil not available, process cleanup will be limited")
    PSUTIL_AVAILABLE = False


def cleanup_process_tree(pid: int, timeout: float = 10.0, force_timeout: float = 5.0) -> bool:
    """
    Clean up a process and all its children.
    
    Args:
        pid: Process ID to clean up
        timeout: Timeout for graceful termination (seconds)
        force_timeout: Timeout for forced termination (seconds)
        
    Returns:
        True if cleanup succeeded, False otherwise
    """
    # Handle invalid PIDs gracefully
    if pid <= 0:
        logger.debug(f"Invalid PID {pid}, cleanup considered successful")
        return True
        
    if platform.system() == "Windows":
        return _cleanup_process_tree_windows(pid, timeout, force_timeout)
    else:
        return _cleanup_process_tree_unix(pid, timeout, force_timeout)


def _cleanup_process_tree_unix(pid: int, timeout: float, force_timeout: float) -> bool:
    """Clean up process tree on Unix systems."""
    try:
        # Check if process exists first
        if not _process_exists(pid):
            logger.debug(f"Process {pid} does not exist, cleanup considered successful")
            return True
            
        # Get process group ID
        try:
            pgid = os.getpgid(pid)
        except OSError as e:
            logger.debug(f"Cannot get process group for PID {pid}: {e}")
            pgid = pid  # Fallback to using the PID itself
        
        # Get all child processes
        children = get_process_children(pid)
        logger.debug(f"Found {len(children)} child processes for PID {pid}")
        
        # Try graceful termination first
        if _terminate_gracefully_unix(pid, pgid, children, timeout):
            logger.debug(f"Graceful termination successful for PID {pid}")
            return True
        
        logger.debug(f"Graceful termination failed, forcing termination for PID {pid}")
        
        # Force termination if graceful failed
        if _force_terminate_unix(pid, pgid, children, force_timeout):
            logger.debug(f"Force termination successful for PID {pid}")
            return True
        
        logger.warning(f"Force termination failed for PID {pid}")
        return False
        
    except Exception as e:
        logger.error(f"Error during process cleanup for PID {pid}: {e}")
        return False


def _terminate_gracefully_unix(pid: int, pgid: int, children: List, timeout: float) -> bool:
    """
    Attempt graceful termination on Unix systems.
    
    Args:
        pid: Process ID
        pgid: Process group ID
        children: List of child processes (if psutil available)
        timeout: Timeout for graceful termination
        
    Returns:
        True if successful
    """
    # Check if process already gone
    if not _process_exists(pid):
        logger.debug(f"Process {pid} already terminated")
        return True
    
    # Send SIGTERM to process group
    try:
        os.killpg(pgid, signal.SIGTERM)
        logger.debug(f"Sent SIGTERM to process group {pgid}")
    except OSError as e:
        logger.debug(f"Cannot send SIGTERM to process group {pgid}: {e}")
        # Try sending to individual process
        try:
            os.kill(pid, signal.SIGTERM)
            logger.debug(f"Sent SIGTERM to process {pid}")
        except OSError as e2:
            logger.debug(f"Cannot send SIGTERM to process {pid}: {e2}")
            # If we can't send the signal, check if process is already gone
            if not _process_exists(pid):
                return True
    
    # Wait for process termination
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not _process_exists(pid):
            return True
        
        # Check if using psutil, wait for children too
        if PSUTIL_AVAILABLE and children:
            all_gone = True
            for child in children:
                try:
                    if child.is_running():
                        all_gone = False
                        break
                except psutil.NoSuchProcess:
                    pass
            if all_gone:
                return True
        
        time.sleep(0.1)
    
    return False


def _force_terminate_unix(pid: int, pgid: int, children: List, timeout: float) -> bool:
    """
    Force termination on Unix systems.
    
    Args:
        pid: Process ID
        pgid: Process group ID  
        children: List of child processes
        timeout: Timeout for forced termination
        
    Returns:
        True if successful
    """
    # Check if process already gone
    if not _process_exists(pid):
        logger.debug(f"Process {pid} already terminated")
        return True
    
    # Send SIGKILL to process group
    try:
        os.killpg(pgid, signal.SIGKILL)
        logger.debug(f"Sent SIGKILL to process group {pgid}")
    except OSError as e:
        logger.debug(f"Cannot send SIGKILL to process group {pgid}: {e}")
        # Try sending to individual process
        try:
            os.kill(pid, signal.SIGKILL)
            logger.debug(f"Sent SIGKILL to process {pid}")
        except OSError as e2:
            logger.debug(f"Cannot send SIGKILL to process {pid}: {e2}")
            # If we can't send the signal, check if process is already gone
            if not _process_exists(pid):
                return True
    
    # Wait for final confirmation
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not _process_exists(pid):
            return True
        time.sleep(0.1)
    
    return False


def _cleanup_process_tree_windows(pid: int, timeout: float, force_timeout: float) -> bool:
    """
    Windows-specific process tree cleanup.
    
    Args:
        pid: Process ID to cleanup
        timeout: Graceful termination timeout
        force_timeout: Forced termination timeout
        
    Returns:
        True if successful
    """
    if not PSUTIL_AVAILABLE:
        logger.error("psutil is required for Windows process cleanup")
        return False
    
    try:
        # Check if process exists
        if not _process_exists(pid):
            logger.debug(f"Process {pid} doesn't exist, cleanup not needed")
            return True
        
        # Get process and all children
        try:
            parent = psutil.Process(pid)
            processes = [parent] + parent.children(recursive=True)
            logger.debug(f"Found {len(processes)} processes to cleanup (including parent)")
        except psutil.NoSuchProcess:
            logger.debug(f"Process {pid} not found")
            return True
        
        # Step 1: Graceful termination
        for proc in processes:
            try:
                proc.terminate()
                logger.debug(f"Terminated process {proc.pid}")
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logger.debug(f"Error terminating process {proc.pid}: {e}")
        
        # Wait for graceful termination
        try:
            gone, still_alive = psutil.wait_procs(processes, timeout=timeout)
            logger.debug(f"Graceful termination: {len(gone)} gone, {len(still_alive)} still alive")
        except Exception as e:
            logger.debug(f"Error waiting for processes: {e}")
            still_alive = processes
        
        # Step 2: Force termination if needed
        if still_alive:
            logger.debug(f"Force killing {len(still_alive)} remaining processes")
            for proc in still_alive:
                try:
                    proc.kill()
                    logger.debug(f"Force killed process {proc.pid}")
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    logger.debug(f"Error force killing process {proc.pid}: {e}")
            
            # Final wait
            try:
                gone, still_alive = psutil.wait_procs(still_alive, timeout=force_timeout)
                logger.debug(f"Force termination: {len(gone)} gone, {len(still_alive)} still alive")
            except Exception as e:
                logger.debug(f"Error in final wait: {e}")
        
        # Check final result
        return not _process_exists(pid)
        
    except Exception as e:
        logger.error(f"Error cleaning up Windows process tree for PID {pid}: {e}")
        raise ProcessCleanupError(pid, str(e))


def _process_exists(pid: int) -> bool:
    """
    Check if a process exists and is actually running.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process exists and is running
    """
    if PSUTIL_AVAILABLE:
        try:
            proc = psutil.Process(pid)
            # Check if process is actually running (not zombie)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    else:
        # Fallback for systems without psutil
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def kill_process_group(pgid: int, sig: int = signal.SIGTERM) -> bool:
    """
    Send signal to an entire process group.
    
    Args:
        pgid: Process group ID
        sig: Signal to send (default: SIGTERM)
        
    Returns:
        True if successful
    """
    try:
        if platform.system() == "Windows":
            logger.warning("Process group signaling not supported on Windows")
            return False
        
        os.killpg(pgid, sig)
        logger.debug(f"Sent signal {sig} to process group {pgid}")
        return True
        
    except OSError as e:
        logger.debug(f"Error sending signal {sig} to process group {pgid}: {e}")
        return False


def get_process_children(pid: int) -> List[int]:
    """
    Get list of child process IDs.
    
    Args:
        pid: Parent process ID
        
    Returns:
        List of child process IDs
    """
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not available, cannot get process children")
        return []
    
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        return [child.pid for child in children]
        
    except psutil.NoSuchProcess:
        return []
    except Exception as e:
        logger.debug(f"Error getting children for process {pid}: {e}")
        return []


def is_process_running(pid: int) -> bool:
    """
    Check if a process is currently running.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process is running
    """
    if not PSUTIL_AVAILABLE:
        return _process_exists(pid)
    
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False
    except Exception:
        # Fallback to basic existence check
        return _process_exists(pid)


def wait_for_process_exit(pid: int, timeout: float = 10.0) -> bool:
    """
    Wait for a process to exit.
    
    Args:
        pid: Process ID to wait for
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if process exited within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not _process_exists(pid):
            return True
        time.sleep(0.1)
    
    return False 