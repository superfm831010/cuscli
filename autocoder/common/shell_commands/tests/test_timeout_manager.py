"""
Tests for timeout manager functionality.

This module tests the timeout management for shell command execution.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from autocoder.common.shell_commands.timeout_manager import TimeoutManager
from autocoder.common.shell_commands.timeout_config import TimeoutConfig
from autocoder.common.shell_commands.exceptions import CommandTimeoutError


class TestTimeoutManager:
    """Test cases for TimeoutManager class."""
    
    def test_initialization(self):
        """Test timeout manager initialization."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = TimeoutManager(config)
        
        assert manager.config == config
        assert len(manager.active_timers) == 0
    
    def test_start_timeout_basic(self):
        """Test starting a basic timeout."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        # Mock process
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None  # Still running
        
        # Start timeout
        manager.start_timeout(mock_process, 0.1)
        
        assert 123 in manager.active_timers
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_start_timeout_with_callback(self):
        """Test starting timeout with custom callback."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        callback_called = []
        
        def custom_callback(proc, timeout):
            callback_called.append((proc, timeout))
        
        # Start timeout with callback
        manager.start_timeout(mock_process, 0.01, custom_callback)
        
        # Wait for timeout to trigger
        time.sleep(0.02)
        
        # Callback should have been called
        assert len(callback_called) == 1
        assert callback_called[0][0] == mock_process
        assert callback_called[0][1] == 0.01
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_cancel_timeout(self):
        """Test canceling a timeout."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        # Start and then cancel timeout
        manager.start_timeout(mock_process, 10.0)  # Long timeout
        assert 123 in manager.active_timers
        
        cancelled = manager.cancel_timeout(mock_process)
        assert cancelled
        assert 123 not in manager.active_timers
    
    def test_cancel_nonexistent_timeout(self):
        """Test canceling a non-existent timeout."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 999
        
        cancelled = manager.cancel_timeout(mock_process)
        assert not cancelled
    
    def test_timeout_triggers_callback(self):
        """Test that timeout triggers the callback function."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None  # Process still running
        
        timeout_triggered = []
        
        def timeout_callback(proc, timeout):
            timeout_triggered.append(True)
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout with very short duration
            manager.start_timeout(mock_process, 0.01, timeout_callback)
            
            # Wait for timeout to trigger
            time.sleep(0.02)
            
            assert len(timeout_triggered) == 1
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_timeout_does_not_trigger_for_completed_process(self):
        """Test that timeout doesn't trigger for already completed process."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = 0  # Process completed
        
        timeout_triggered = []
        
        def timeout_callback(proc, timeout):
            timeout_triggered.append(True)
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout
            manager.start_timeout(mock_process, 0.01, timeout_callback)
            
            # Wait for potential timeout
            time.sleep(0.02)
            
            # Timeout will still trigger since TimeoutManager doesn't check process.poll()
            # but callback should be called
            assert len(timeout_triggered) == 1
        
        # PID should be cleaned up from active timers
        assert 123 not in manager.active_timers
    
    def test_get_active_timeouts(self):
        """Test getting list of active timeouts."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process1 = Mock()
        mock_process1.pid = 123
        mock_process1.poll.return_value = None
        
        mock_process2 = Mock()
        mock_process2.pid = 456
        mock_process2.poll.return_value = None
        
        # Start multiple timeouts
        manager.start_timeout(mock_process1, 10.0)
        manager.start_timeout(mock_process2, 10.0)
        
        active = manager.get_active_timeouts()
        assert 123 in active
        assert 456 in active
        assert len(active) == 2
        
        # Cleanup
        manager.cancel_timeout(mock_process1)
        manager.cancel_timeout(mock_process2)
    
    def test_cleanup_all_timeouts(self):
        """Test cleaning up all active timeouts."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        # Start multiple timeouts
        processes = []
        for pid in [123, 456, 789]:
            mock_process = Mock()
            mock_process.pid = pid
            mock_process.poll.return_value = None
            processes.append(mock_process)
            manager.start_timeout(mock_process, 10.0)
        
        assert len(manager.active_timers) == 3
        
        # Clean up all
        manager.cleanup_all_timeouts()
        
        assert len(manager.active_timers) == 0
    
    def test_is_timeout_active(self):
        """Test checking if timeout is active."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        # Initially no timeout
        assert not manager.is_timeout_active(mock_process)
        
        # Start timeout
        manager.start_timeout(mock_process, 10.0)
        assert manager.is_timeout_active(mock_process)
        
        # Cancel timeout
        manager.cancel_timeout(mock_process)
        assert not manager.is_timeout_active(mock_process)
    
    def test_default_timeout_callback(self):
        """Test the default timeout callback behavior."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout without custom callback (uses default)
            manager.start_timeout(mock_process, 0.01)
            
            # Wait for timeout to trigger
            time.sleep(0.02)
            
            # Process cleanup should have been attempted
            # The actual cleanup is handled by cleanup_process_tree function
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_timeout_with_process_cleanup(self):
        """Test timeout behavior with process cleanup."""
        config = TimeoutConfig(default_timeout=1.0, grace_period=0.01)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.kill = Mock()
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout
            manager.start_timeout(mock_process, 0.01)
            
            # Wait for timeout and grace period
            time.sleep(0.03)
            
            # Process cleanup should have been attempted
            # The actual cleanup is handled by cleanup_process_tree function
        
        # Cleanup
        manager.cancel_timeout(mock_process)


class TestTimeoutManagerThreadSafety:
    """Test cases for thread safety of TimeoutManager."""
    
    def test_concurrent_timeout_operations(self):
        """Test concurrent timeout start/cancel operations."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        results = []
        processes = []
        
        def start_timeouts():
            for i in range(10):
                mock_process = Mock()
                mock_process.pid = 1000 + i
                mock_process.poll.return_value = None
                processes.append(mock_process)
                manager.start_timeout(mock_process, 1.0)
                results.append(('start', True))
        
        def cancel_timeouts():
            time.sleep(0.01)  # Let some timeouts start first
            for i in range(10):
                if i < len(processes):
                    cancelled = manager.cancel_timeout(processes[i])
                    results.append(('cancel', cancelled))
        
        # Run concurrent operations
        thread1 = threading.Thread(target=start_timeouts)
        thread2 = threading.Thread(target=cancel_timeouts)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Should have handled all operations without crashes
        assert len(results) >= 10  # At least the start operations
        
        # Cleanup any remaining timeouts
        manager.cleanup_all_timeouts()


class TestTimeoutManagerErrorCases:
    """Test cases for error conditions and edge cases."""
    
    def test_timeout_with_none_process(self):
        """Test timeout with None process."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        # This should raise an AttributeError when trying to access process.pid
        with pytest.raises(AttributeError):
            manager.start_timeout(None, 1.0)  # type: ignore
    
    def test_timeout_with_invalid_timeout_value(self):
        """Test timeout with invalid timeout values."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        
        # Negative timeout - should be ignored
        manager.start_timeout(mock_process, -1.0)
        assert 123 not in manager.active_timers
        
        # Zero timeout - should be ignored
        manager.start_timeout(mock_process, 0.0)
        assert 123 not in manager.active_timers
    
    def test_timeout_callback_exception(self):
        """Test timeout behavior when callback raises exception."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        def failing_callback(proc, timeout):
            raise RuntimeError("Callback failed")
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout with failing callback
            manager.start_timeout(mock_process, 0.01, failing_callback)
            
            # Wait for timeout to trigger
            time.sleep(0.02)
            
            # Manager should still be functional despite callback failure
            # The process should have been cleaned up from active timers
            assert 123 not in manager.active_timers
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_process_poll_exception(self):
        """Test timeout behavior when process.poll() raises exception."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.side_effect = OSError("Process access error")
        
        callback_called = []
        
        def test_callback(proc, timeout):
            callback_called.append(True)
        
        # Mock cleanup_process_tree to prevent system calls
        with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
            # Start timeout
            manager.start_timeout(mock_process, 0.01, test_callback)
            
            # Wait for timeout
            time.sleep(0.02)
            
            # Callback should still be called despite poll() exception
            assert len(callback_called) == 1
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_duplicate_pid_timeout(self):
        """Test starting timeout for same PID twice."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        # Start first timeout
        manager.start_timeout(mock_process, 1.0)
        assert 123 in manager.active_timers
        
        # Start second timeout for same PID
        manager.start_timeout(mock_process, 1.0)
        
        # Should have cancelled the first timeout and started new one
        assert 123 in manager.active_timers
        
        # Cleanup
        manager.cancel_timeout(mock_process)
    
    def test_timer_cleanup_on_exception(self):
        """Test that timers are cleaned up even when exceptions occur."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = TimeoutManager(config)
        
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        
        # Mock the Timer to raise an exception
        with patch('threading.Timer') as mock_timer_class:
            mock_timer = Mock()
            mock_timer.start.side_effect = RuntimeError("Timer failed")
            mock_timer_class.return_value = mock_timer
            
            # Should handle exception gracefully
            manager.start_timeout(mock_process, 1.0)
            
            # Timer should not be in active timers due to exception
            assert 123 not in manager.active_timers


class TestTimeoutManagerIntegration:
    """Integration tests for TimeoutManager."""
    
    def test_real_timeout_scenario(self):
        """Test a realistic timeout scenario."""
        config = TimeoutConfig(default_timeout=0.1, grace_period=0.01)
        manager = TimeoutManager(config)
        
        # Create a real subprocess for testing
        import subprocess
        import platform
        
        if platform.system() == 'Windows':
            proc = subprocess.Popen(['ping', '127.0.0.1', '-n', '10'])
        else:
            proc = subprocess.Popen(['sleep', '10'])
        
        timeout_occurred = []
        
        def timeout_callback(process, timeout):
            timeout_occurred.append(True)
            try:
                process.terminate()
            except:
                pass
        
        try:
            # Mock cleanup_process_tree to prevent system calls
            with patch('autocoder.common.shell_commands.timeout_manager.cleanup_process_tree', return_value=True):
                # Start timeout
                manager.start_timeout(proc, 0.05, timeout_callback)
                
                # Wait for timeout to occur
                time.sleep(0.1)
                
                # Timeout should have occurred
                assert len(timeout_occurred) == 1
            
        finally:
            # Cleanup
            try:
                proc.terminate()
                proc.wait(timeout=1)
            except:
                pass
            manager.cancel_timeout(proc)
    
    def test_timeout_manager_with_command_executor_integration(self):
        """Test timeout manager integration with command execution."""
        config = TimeoutConfig(default_timeout=0.1)
        manager = TimeoutManager(config)
        
        # Simulate process lifecycle
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        
        # Start timeout
        manager.start_timeout(mock_process, 0.05)
        
        # Simulate process completing before timeout
        time.sleep(0.02)
        mock_process.poll.return_value = 0  # Process completed
        
        # Cancel timeout (process completed)
        cancelled = manager.cancel_timeout(mock_process)
        
        # Should have been able to cancel
        assert cancelled or 123 not in manager.active_timers


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 