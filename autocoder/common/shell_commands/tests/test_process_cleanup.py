"""
Tests for process cleanup functionality.

This module tests the process cleanup mechanisms used in shell command execution.
"""

import pytest
import os
import platform
import time
from unittest.mock import Mock, patch, MagicMock
import subprocess

from autocoder.common.shell_commands.process_cleanup import (
    cleanup_process_tree,
    kill_process_group,
    get_process_children,
    is_process_running,
    wait_for_process_exit
)
from autocoder.common.shell_commands.exceptions import (
    ProcessCleanupError,
    ProcessNotFoundError
)


class TestProcessCleanup:
    """Test cases for process cleanup functionality."""
    
    def test_cleanup_process_tree_nonexistent_process(self):
        """Test cleanup of non-existent process."""
        # Use a PID that's very unlikely to exist
        fake_pid = 999999
        
        # Should handle gracefully
        result = cleanup_process_tree(fake_pid)
        assert result is True  # Should return True if process doesn't exist
    
    def test_cleanup_process_tree_with_timeout(self):
        """Test cleanup with custom timeout."""
        # Create a simple process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(["sleep", "0.1"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        
        pid = process.pid
        
        # Wait for process to finish naturally
        time.sleep(0.2)
        
        # Cleanup should succeed
        result = cleanup_process_tree(pid, timeout=1.0)
        assert result is True
        
        # Ensure process is terminated
        process.wait()
    
    def test_cleanup_process_tree_already_terminated(self):
        """Test cleanup of already terminated process."""
        # Create and immediately terminate a process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["echo", "test"])
        
        pid = process.pid
        process.wait()  # Wait for it to finish
        
        # Cleanup should succeed
        result = cleanup_process_tree(pid)
        assert result is True
    
    @patch('autocoder.common.shell_commands.process_cleanup.psutil')
    @patch('autocoder.common.shell_commands.process_cleanup.os.kill')
    def test_cleanup_process_tree_kill_failure(self, mock_kill, mock_psutil):
        """Test cleanup when kill fails."""
        # Mock psutil to make it seem like process exists but can't be killed
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = True
        mock_proc.status.return_value = 'running'
        mock_psutil.Process.return_value = mock_proc
        mock_psutil.STATUS_ZOMBIE = 'zombie'
        
        # Mock os.kill to raise an exception
        mock_kill.side_effect = OSError("Permission denied")
        
        # Should handle the error gracefully
        result = cleanup_process_tree(1234)
        assert result is False  # Should return False when cleanup fails
    
    def test_cleanup_process_tree_with_children(self):
        """Test cleanup of process with children."""
        # This test is complex and depends on psutil availability
        # For now, just test that the function can be called
        result = cleanup_process_tree(999999)  # Non-existent PID
        assert result is True


class TestKillProcessGroup:
    """Test cases for kill_process_group function."""
    
    def test_kill_process_group_nonexistent(self):
        """Test killing non-existent process group."""
        # Use a PGID that's very unlikely to exist
        fake_pgid = 999999
        
        # Should handle gracefully
        result = kill_process_group(fake_pgid)
        assert result is False  # Should return False if group doesn't exist
    
    @patch('autocoder.common.shell_commands.process_cleanup.os.killpg')
    def test_kill_process_group_success(self, mock_killpg):
        """Test successful process group killing."""
        # Mock successful killpg
        mock_killpg.return_value = None
        
        result = kill_process_group(1234)
        assert result is True
        mock_killpg.assert_called_once()
    
    @patch('autocoder.common.shell_commands.process_cleanup.os.killpg')
    def test_kill_process_group_failure(self, mock_killpg):
        """Test failed process group killing."""
        # Mock failed killpg
        mock_killpg.side_effect = OSError("No such process")
        
        result = kill_process_group(1234)
        assert result is False
        mock_killpg.assert_called_once()
    
    def test_kill_process_group_with_custom_signal(self):
        """Test killing process group with custom signal."""
        import signal
        
        # Should handle custom signal
        result = kill_process_group(999999, signal.SIGTERM)
        assert result is False  # Non-existent group should fail


class TestGetProcessChildren:
    """Test cases for get_process_children function."""
    
    def test_get_process_children_nonexistent(self):
        """Test getting children of non-existent process."""
        fake_pid = 999999
        
        children = get_process_children(fake_pid)
        assert children == []  # Should return empty list
    
    def test_get_process_children_no_children(self):
        """Test getting children of process with no children."""
        # Create a simple process with no children
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["echo", "test"])
        
        pid = process.pid
        
        children = get_process_children(pid)
        assert isinstance(children, list)
        
        # Clean up
        process.wait()
    
    @patch('autocoder.common.shell_commands.process_cleanup.PSUTIL_AVAILABLE', False)
    def test_get_process_children_without_psutil(self):
        """Test getting children when psutil is not available."""
        children = get_process_children(1234)
        assert children == []  # Should return empty list without psutil


class TestIsProcessRunning:
    """Test cases for is_process_running function."""
    
    def test_is_process_running_nonexistent(self):
        """Test checking non-existent process."""
        fake_pid = 999999
        
        result = is_process_running(fake_pid)
        assert result is False
    
    def test_is_process_running_existing(self):
        """Test checking existing process."""
        # Create a short-lived process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["sleep", "0.1"])
        
        pid = process.pid
        
        # Should be running initially
        result = is_process_running(pid)
        assert result is True
        
        # Wait for process to finish
        process.wait()
        
        # Should not be running after completion
        result = is_process_running(pid)
        assert result is False
    
    def test_is_process_running_current_process(self):
        """Test checking current process."""
        current_pid = os.getpid()
        
        result = is_process_running(current_pid)
        assert result is True


class TestWaitForProcessExit:
    """Test cases for wait_for_process_exit function."""
    
    def test_wait_for_process_exit_nonexistent(self):
        """Test waiting for non-existent process."""
        fake_pid = 999999
        
        result = wait_for_process_exit(fake_pid, timeout=0.1)
        assert result is True  # Should return True if process doesn't exist
    
    def test_wait_for_process_exit_quick_process(self):
        """Test waiting for quick process."""
        # Create a quick process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["echo", "test"])
        
        pid = process.pid
        
        # Should exit quickly
        result = wait_for_process_exit(pid, timeout=5.0)
        assert result is True
        
        # Ensure process is done
        process.wait()
    
    def test_wait_for_process_exit_timeout(self):
        """Test waiting for process with timeout."""
        # Create a longer-running process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "10", "127.0.0.1"])
        else:
            process = subprocess.Popen(["sleep", "1"])
        
        pid = process.pid
        
        # Should timeout
        result = wait_for_process_exit(pid, timeout=0.1)
        assert result is False
        
        # Clean up
        process.terminate()
        process.wait()
    
    def test_wait_for_process_exit_zero_timeout(self):
        """Test waiting with zero timeout."""
        # Create a process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["echo", "test"])
        
        pid = process.pid
        
        # Zero timeout should return immediately
        result = wait_for_process_exit(pid, timeout=0.0)
        assert result is False  # Should timeout immediately
        
        # Clean up
        process.wait()


class TestProcessCleanupIntegration:
    """Test cases for process cleanup integration scenarios."""
    
    def test_full_cleanup_workflow(self):
        """Test complete cleanup workflow."""
        # Create a process
        if platform.system() == "Windows":
            process = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
        else:
            process = subprocess.Popen(["echo", "test"])
        
        pid = process.pid
        
        # Verify process is running
        assert is_process_running(pid) is True
        
        # Wait for natural exit
        process.wait()
        
        # Cleanup should succeed
        result = cleanup_process_tree(pid)
        assert result is True
        
        # Verify process is not running
        assert is_process_running(pid) is False
    
    def test_cleanup_with_error_handling(self):
        """Test cleanup with error handling."""
        # Test with invalid PID
        invalid_pid = -1
        
        # Should handle gracefully
        result = cleanup_process_tree(invalid_pid)
        assert result is True  # Should succeed for invalid PID
    
    def test_cleanup_performance(self):
        """Test cleanup performance with reasonable timeout."""
        # Create multiple quick processes
        processes = []
        pids = []
        
        for i in range(3):
            if platform.system() == "Windows":
                proc = subprocess.Popen(["ping", "-n", "1", "127.0.0.1"])
            else:
                proc = subprocess.Popen(["echo", f"test{i}"])
            
            processes.append(proc)
            pids.append(proc.pid)
        
        # Wait for all to complete
        for proc in processes:
            proc.wait()
        
        # Cleanup should be fast
        start_time = time.time()
        
        for pid in pids:
            cleanup_process_tree(pid)
        
        elapsed = time.time() - start_time
        assert elapsed < 5.0  # Should complete within 5 seconds


class TestProcessCleanupEdgeCases:
    """Test cases for edge cases in process cleanup."""
    
    def test_cleanup_with_negative_pid(self):
        """Test cleanup with negative PID."""
        result = cleanup_process_tree(-1)
        assert result is True  # Should handle gracefully
    
    def test_cleanup_with_zero_pid(self):
        """Test cleanup with zero PID."""
        result = cleanup_process_tree(0)
        assert result is True  # Should handle gracefully
    
    def test_cleanup_with_very_large_pid(self):
        """Test cleanup with very large PID."""
        result = cleanup_process_tree(999999999)
        assert result is True  # Should handle gracefully
    
    def test_cleanup_with_negative_timeout(self):
        """Test cleanup with negative timeout."""
        result = cleanup_process_tree(999999, timeout=-1.0)
        assert result is True  # Should handle gracefully
    
    def test_cleanup_with_zero_timeout(self):
        """Test cleanup with zero timeout."""
        result = cleanup_process_tree(999999, timeout=0.0)
        assert result is True  # Should handle gracefully
    
    def test_concurrent_cleanup_calls(self):
        """Test concurrent cleanup calls."""
        import threading
        
        results = []
        
        def cleanup_worker(pid):
            result = cleanup_process_tree(pid)
            results.append(result)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=cleanup_worker, args=(999999 + i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(results)
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 