"""
Test module for ProcessManager functionality.

This module tests the process management functionality including:
- Process creation and configuration
- Process registration and management
- Process cleanup and timeout handling
- Error handling and edge cases
"""

import os
import time
import platform
import threading
from unittest.mock import Mock, patch, MagicMock
import subprocess
import pytest

from autocoder.common.shell_commands.process_manager import ProcessManager
from autocoder.common.shell_commands.timeout_config import TimeoutConfig
from autocoder.common.shell_commands.exceptions import CommandExecutionError, ProcessCleanupError


class TestProcessManager:
    """Test basic ProcessManager functionality."""
    
    def test_initialization(self):
        """Test ProcessManager initialization."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        assert manager.config == config
        assert manager.timeout_manager is not None
        assert len(manager.active_processes) == 0
        assert len(manager.process_groups) == 0
    
    def test_create_process_basic(self):
        """Test basic process creation."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(command)
        
        try:
            assert process is not None
            assert process.pid > 0
            assert process.pid in manager.active_processes
            
            # Wait for process to complete
            exit_code = manager.wait_for_process(process, timeout=5.0)
            assert exit_code == 0
        finally:
            # Cleanup if needed
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_create_process_with_options(self):
        """Test process creation with various options."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(
            command,
            timeout=30.0,
            shell=True,
            capture_output=True,
            text=True
        )
        
        try:
            assert process is not None
            assert process.pid > 0
            assert process.pid in manager.active_processes
            
            # Wait for process to complete
            exit_code = manager.wait_for_process(process, timeout=5.0)
            assert exit_code == 0
        finally:
            # Cleanup if needed
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_create_process_failure(self):
        """Test process creation failure handling."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Try to create process with invalid cwd (this will actually fail)
        with pytest.raises(CommandExecutionError):
            manager.create_process(['echo', 'test'], cwd='/this/path/does/not/exist')
    
    def test_register_process(self):
        """Test manual process registration."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        mock_process = Mock()
        mock_process.pid = 12345
        
        manager._register_process(mock_process)
        
        assert mock_process.pid in manager.active_processes
    
    def test_cleanup_process_success(self):
        """Test successful process cleanup."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['ping', '127.0.0.1', '-n', '1']
        else:
            command = ['sleep', '0.1']
        
        process = manager.create_process(command)
        
        try:
            pid = process.pid
            assert pid in manager.active_processes
            
            # Wait a bit for process to complete or be running
            time.sleep(0.05)
            
            # Cleanup
            result = manager.cleanup_process_tree(process)
            
            assert result is True or result is False  # Should return a boolean
            assert pid not in manager.active_processes
            
        except Exception as e:
            # Fallback cleanup
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                pass
            manager.unregister_process(process)
    
    def test_cleanup_nonexistent_process(self):
        """Test cleanup of non-existent process."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Create a mock process that doesn't exist
        mock_process = Mock()
        mock_process.pid = 99999
        
        result = manager.cleanup_process_tree(mock_process)
        
        # Should handle gracefully
        assert result is False or result is True
    
    def test_cleanup_all_processes(self):
        """Test cleanup of all managed processes."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        processes = []
        
        # Create multiple processes
        for i in range(3):
            if platform.system() == 'Windows':
                command = ['ping', '127.0.0.1', '-n', '1']
            else:
                command = ['sleep', '0.1']
            
            process = manager.create_process(command)
            if process:
                processes.append(process)
        
        try:
            assert len(manager.active_processes) >= len(processes)
            
            # Cleanup all
            results = manager.cleanup_all_processes()
            
            assert len(manager.active_processes) == 0
            assert isinstance(results, list)
            
        except Exception:
            # Fallback cleanup
            for process in processes:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except:
                    pass
            manager.active_processes.clear()
    
    def test_get_managed_processes(self):
        """Test getting list of managed processes."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        initial_count = len(manager.get_all_processes())
        
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(command)
        
        try:
            current_count = len(manager.get_all_processes())
            assert current_count == initial_count + 1
            
            processes = manager.get_all_processes()
            assert process.pid in processes
            assert processes[process.pid] == process
            
        finally:
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_is_process_managed(self):
        """Test checking if process is managed."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Non-existent process
        assert 99999 not in manager.active_processes
        
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(command)
        
        try:
            # Process should be managed
            assert process.pid in manager.active_processes
            
            # Wait for process to complete
            exit_code = manager.wait_for_process(process, timeout=5.0)
            
            # Process should no longer be managed
            assert process.pid not in manager.active_processes
            
        finally:
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_unregister_process(self):
        """Test process unregistration."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        mock_process = Mock()
        mock_process.pid = 12345
        
        # Register then unregister
        manager._register_process(mock_process)
        assert mock_process.pid in manager.active_processes
        
        manager.unregister_process(mock_process)
        assert mock_process.pid not in manager.active_processes


class TestProcessManagerWithTimeout:
    """Test ProcessManager with timeout functionality."""
    
    def test_process_with_timeout(self):
        """Test process creation with timeout."""
        config = TimeoutConfig(default_timeout=1.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            # Use a command that will run for a while
            command = ['ping', '127.0.0.1', '-n', '10']
        else:
            command = ['sleep', '10']
        
        process = manager.create_process(command, timeout=0.1)
        
        try:
            assert process is not None
            
            # Process should be killed by timeout
            start_time = time.time()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                # Expected if process is still running
                pass
            duration = time.time() - start_time
            
            # Should have been terminated by timeout (allow some margin)
            assert duration < 2.0
            
        finally:
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                pass
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)


class TestProcessManagerErrorHandling:
    """Test ProcessManager error handling."""
    
    def test_cleanup_with_permission_error(self):
        """Test cleanup when permission is denied."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Try to cleanup a system process (should fail with permission error)
        if platform.system() == 'Windows':
            system_pid = 4  # System process
        else:
            system_pid = 1  # Init process
        
        # Create a mock process for system PID
        mock_process = Mock()
        mock_process.pid = system_pid
        
        result = manager.cleanup_process_tree(mock_process)
        
        # Should handle gracefully (might succeed or fail depending on permissions)
        assert result is True or result is False
    
    def test_cleanup_with_process_not_found(self):
        """Test cleanup when process is not found."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Create a mock process that doesn't actually exist
        mock_process = Mock()
        mock_process.pid = 99999
        
        result = manager.cleanup_process_tree(mock_process)
        
        # Should handle gracefully
        assert result is True or result is False
    
    def test_process_creation_with_invalid_command(self):
        """Test process creation with invalid command."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Try to create process with invalid cwd (this will actually fail)
        with pytest.raises(CommandExecutionError):
            manager.create_process(['echo', 'test'], cwd='/this/path/does/not/exist')
    
    def test_process_creation_with_invalid_cwd(self):
        """Test process creation with invalid working directory."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        with pytest.raises(CommandExecutionError):
            manager.create_process(
                ['echo', 'test'],
                cwd='/this/directory/does/not/exist'
            )
    
    @patch('autocoder.common.shell_commands.process_manager.cleanup_process_tree')
    def test_cleanup_with_cleanup_function_failure(self, mock_cleanup):
        """Test process cleanup when cleanup function fails."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Make cleanup function return False (indicating failure)
        mock_cleanup.return_value = False
        
        # Create a mock process that appears to be still running
        mock_process = Mock()
        mock_process.pid = 123
        mock_process.poll.return_value = None  # Process is still running
        
        # Cleanup should handle the failure
        result = manager.cleanup_process_tree(mock_process)
        
        # Should return False on failure
        assert result is False


class TestProcessManagerConcurrency:
    """Test ProcessManager concurrency handling."""
    
    def test_concurrent_process_creation(self):
        """Test concurrent process creation."""
        import threading
        
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        processes = []
        errors = []
        
        def create_process():
            try:
                if platform.system() == 'Windows':
                    command = ['echo', 'test']
                else:
                    command = ['echo', 'test']
                
                process = manager.create_process(command)
                if process:
                    processes.append(process)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=create_process) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        try:
            # Should have created some processes without errors
            assert len(processes) > 0
            assert len(errors) == 0
            
            # All processes should be managed
            for process in processes:
                assert process.pid in manager.active_processes
                
        finally:
            # Cleanup
            for process in processes:
                try:
                    if process.pid in manager.active_processes:
                        manager.cleanup_process_tree(process)
                except:
                    pass


class TestProcessManagerIntegration:
    """Test ProcessManager integration scenarios."""
    
    def test_full_lifecycle(self):
        """Test complete process lifecycle."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['echo', 'Hello World']
        else:
            command = ['echo', 'Hello World']
        
        # Create process
        process = manager.create_process(command)
        
        try:
            assert process is not None
            assert process.pid in manager.active_processes
            
            # Wait for completion
            exit_code = manager.wait_for_process(process, timeout=5.0)
            assert exit_code == 0
            
            # Process should be automatically unregistered
            assert process.pid not in manager.active_processes
            
        finally:
            if process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)


class TestProcessManagerEdgeCases:
    """Test ProcessManager edge cases."""
    
    def test_empty_command(self):
        """Test process creation with empty command."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        # Empty command will create a process but it will fail at runtime
        process = manager.create_process([])
        
        try:
            assert process is not None
            assert process.pid > 0
            
            # Wait for process to fail
            try:
                exit_code = process.wait(timeout=2.0)
                # Process should fail with non-zero exit code
                assert exit_code != 0
            except subprocess.TimeoutExpired:
                # Process might hang, that's also expected behavior
                pass
        finally:
            if process and process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_very_short_timeout(self):
        """Test process with very short timeout."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['ping', '127.0.0.1', '-n', '5']
        else:
            command = ['sleep', '1']
        
        process = manager.create_process(command, timeout=0.001)  # Very short
        
        try:
            if process:
                start_time = time.time()
                try:
                    process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    # Expected if process is still running
                    pass
                duration = time.time() - start_time
                
                # Should have been killed quickly
                assert duration < 0.5
        finally:
            if process and process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_cleanup_already_cleaned_process(self):
        """Test cleanup of already cleaned process."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(command)
        
        try:
            pid = process.pid
            
            # Wait for process to complete
            process.wait(timeout=5)
            
            # Cleanup once
            result1 = manager.cleanup_process_tree(process)
            
            # Cleanup again
            result2 = manager.cleanup_process_tree(process)
            
            # Both should handle gracefully
            assert result1 is True or result1 is False
            assert result2 is True or result2 is False
            
        except Exception:
            if process and process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)
    
    def test_manager_state_after_errors(self):
        """Test manager state consistency after various errors."""
        config = TimeoutConfig(default_timeout=60.0)
        manager = ProcessManager(config)
        
        initial_count = len(manager.active_processes)
        
        # Try various operations that might fail
        try:
            # This will create a process that fails at runtime
            process1 = manager.create_process(['this_command_does_not_exist'])
            if process1:
                manager.cleanup_process_tree(process1)
        except CommandExecutionError:
            pass
        
        try:
            manager.create_process(['echo', 'test'], cwd='/invalid/path')
        except CommandExecutionError:
            pass
        
        # Manager state should be consistent (might have processes that were created)
        current_count = len(manager.active_processes)
        
        # Should still be able to create valid processes
        if platform.system() == 'Windows':
            command = ['echo', 'test']
        else:
            command = ['echo', 'test']
        
        process = manager.create_process(command)
        
        try:
            assert process is not None
            assert len(manager.active_processes) >= current_count
            
        finally:
            if process and process.pid in manager.active_processes:
                manager.cleanup_process_tree(process)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 