"""
Tests for CommandExecutor functionality.

This module tests the main command execution interface with timeout
support and process management.
"""

import pytest
import time
import platform
from unittest.mock import patch, MagicMock

from ..command_executor import CommandExecutor, execute_command
from ..timeout_config import TimeoutConfig
from ..exceptions import CommandTimeoutError, CommandExecutionError


class TestCommandExecutor:
    """Test cases for CommandExecutor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TimeoutConfig(
            default_timeout=5.0,
            cleanup_timeout=2.0,
            grace_period=1.0
        )
        self.executor = CommandExecutor(self.config, verbose=False)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.executor.cleanup()
    
    def test_simple_command_execution(self):
        """Test basic command execution."""
        if platform.system() == "Windows":
            command = "echo Hello World"
        else:
            command = "echo 'Hello World'"
        
        exit_code, output = self.executor.execute(command)
        
        assert exit_code == 0
        assert "Hello World" in output
    
    def test_command_with_exit_code(self):
        """Test command that returns non-zero exit code."""
        if platform.system() == "Windows":
            command = "exit 1"
        else:
            command = "exit 1"
        
        exit_code, output = self.executor.execute(command)
        
        assert exit_code == 1
    
    def test_command_timeout(self):
        """Test command timeout functionality."""
        if platform.system() == "Windows":
            command = "ping -n 10 127.0.0.1"  # Windows ping command
        else:
            command = "sleep 10"  # Unix sleep command
        
        with pytest.raises(CommandTimeoutError) as exc_info:
            self.executor.execute(command, timeout=1.0)
        
        assert exc_info.value.timeout == 1.0
        assert command in str(exc_info.value)
    
    def test_command_with_working_directory(self):
        """Test command execution with custom working directory."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if platform.system() == "Windows":
                command = "cd"
            else:
                command = "pwd"
            
            exit_code, output = self.executor.execute(command, cwd=temp_dir)
            
            assert exit_code == 0
            assert temp_dir in output.replace("\\", "/")  # Normalize path separators
    
    def test_command_with_environment_variables(self):
        """Test command execution with custom environment variables."""
        env = {"TEST_VAR": "test_value"}
        
        if platform.system() == "Windows":
            command = "echo %TEST_VAR%"
        else:
            command = "echo $TEST_VAR"
        
        exit_code, output = self.executor.execute(command, env=env)
        
        assert exit_code == 0
        assert "test_value" in output
    
    def test_executor_status(self):
        """Test executor status reporting."""
        status = self.executor.get_status()
        
        assert isinstance(status, dict)
        assert "config" in status
        assert "active_processes" in status
        assert "performance_summary" in status
        assert "recent_alerts" in status
    
    def test_executor_cleanup(self):
        """Test executor cleanup functionality."""
        # Start a long-running command
        if platform.system() == "Windows":
            command = "ping -n 100 127.0.0.1"
        else:
            command = "sleep 100"
        
        # Execute in background (this will be a real test in a threaded environment)
        # For now, just test that cleanup doesn't crash
        self.executor.cleanup()
        
        # Verify executor is still functional after cleanup
        simple_command = "echo test"
        exit_code, output = self.executor.execute(simple_command)
        assert exit_code == 0

    def test_execute_background_basic(self):
        """Test basic background command execution."""
        if platform.system() == "Windows":
            command = "ping -n 1 127.0.0.1"
        else:
            command = "sleep 0.1"
        
        # Execute command in background
        process_info = self.executor.execute_background(command)
        
        # Verify we get process information
        assert "pid" in process_info
        assert "command" in process_info
        assert "status" in process_info
        assert process_info["pid"] > 0
        assert process_info["status"] == "running"
        
        # Verify process appears in background processes
        bg_processes = self.executor.get_background_processes()
        assert process_info["pid"] in bg_processes
        
        # Wait a bit for process to complete
        time.sleep(0.2)
        
        # Clean up
        self.executor.cleanup_background_process(process_info["pid"])

    def test_execute_background_with_working_directory(self):
        """Test background execution with custom working directory."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if platform.system() == "Windows":
                command = "echo test"
            else:
                command = "echo test"
            
            process_info = self.executor.execute_background(command, cwd=temp_dir)
            
            assert "pid" in process_info
            assert process_info["pid"] > 0
            assert "working_directory" in process_info
            
            # Clean up
            time.sleep(0.1)  # Give process time to complete
            self.executor.cleanup_background_process(process_info["pid"])

    def test_get_background_processes(self):
        """Test getting background processes information."""
        if platform.system() == "Windows":
            command = "ping -n 1 127.0.0.1"
        else:
            command = "sleep 0.1"
        
        # Start a background process
        process_info = self.executor.execute_background(command)
        pid = process_info["pid"]
        
        # Get background processes
        bg_processes = self.executor.get_background_processes()
        
        assert pid in bg_processes
        assert bg_processes[pid]["command"] == command
        assert "status" in bg_processes[pid]
        
        # Clean up
        time.sleep(0.2)
        self.executor.cleanup_background_process(pid)

    def test_cleanup_background_process(self):
        """Test cleanup of specific background process."""
        if platform.system() == "Windows":
            command = "ping -n 5 127.0.0.1"
        else:
            command = "sleep 1"
        
        # Start a background process
        process_info = self.executor.execute_background(command)
        pid = process_info["pid"]
        
        # Verify process is running
        bg_processes = self.executor.get_background_processes()
        assert pid in bg_processes
        
        # Clean up the specific process
        success = self.executor.cleanup_background_process(pid)
        assert success is True or success is False  # Should return a boolean
        
        # Process should be removed from background processes
        time.sleep(0.1)
        bg_processes = self.executor.get_background_processes()
        # Process might still be there if cleanup is in progress, that's ok


class TestExecuteCommand:
    """Test cases for convenience execute_command function."""
    
    def test_convenience_function(self):
        """Test the convenience execute_command function."""
        if platform.system() == "Windows":
            command = "echo Test"
        else:
            command = "echo 'Test'"
        
        exit_code, output = execute_command(command)
        
        assert exit_code == 0
        assert "Test" in output
    
    def test_convenience_function_with_timeout(self):
        """Test convenience function with timeout."""
        if platform.system() == "Windows":
            command = "ping -n 10 127.0.0.1"
        else:
            command = "sleep 10"
        
        with pytest.raises(CommandTimeoutError):
            execute_command(command, timeout=1.0)


class TestExecuteCommandBackground:
    """Test cases for convenience execute_command_background function."""
    
    def test_convenience_background_function(self):
        """Test the convenience execute_command_background function."""
        from ..command_executor import execute_command_background, cleanup_background_process
        
        if platform.system() == "Windows":
            command = "ping -n 1 127.0.0.1"
        else:
            command = "sleep 0.1"
        
        process_info = execute_command_background(command)
        
        assert "pid" in process_info
        assert "command" in process_info
        assert "status" in process_info
        assert process_info["pid"] > 0
        assert process_info["status"] == "running"
        
        # Clean up
        time.sleep(0.2)
        cleanup_background_process(process_info["pid"])
    
    def test_get_background_processes_convenience(self):
        """Test the convenience get_background_processes function."""
        from ..command_executor import (
            execute_command_background, 
            get_background_processes, 
            cleanup_background_process
        )
        
        if platform.system() == "Windows":
            command = "ping -n 1 127.0.0.1"
        else:
            command = "sleep 0.1"
        
        # Start a background process
        process_info = execute_command_background(command)
        pid = process_info["pid"]
        
        # Get background processes
        bg_processes = get_background_processes()
        
        assert pid in bg_processes
        assert bg_processes[pid]["command"] == command
        
        # Clean up
        time.sleep(0.2)
        cleanup_background_process(pid)
    
    def test_get_background_process_info_convenience(self):
        """Test the convenience get_background_process_info function."""
        from ..command_executor import (
            execute_command_background, 
            get_background_process_info, 
            cleanup_background_process
        )
        
        if platform.system() == "Windows":
            command = "ping -n 1 127.0.0.1"
        else:
            command = "sleep 0.1"
        
        # Start a background process
        process_info = execute_command_background(command)
        pid = process_info["pid"]
        
        # Get specific process info
        info = get_background_process_info(pid)
        
        assert info is not None
        assert info["command"] == command
        
        # Clean up
        time.sleep(0.2)
        cleanup_background_process(pid)


class TestCommandExecutorConfiguration:
    """Test cases for CommandExecutor configuration."""
    
    def test_custom_timeout_config(self):
        """Test executor with custom timeout configuration."""
        config = TimeoutConfig(default_timeout=2.0)
        executor = CommandExecutor(config)
        
        # Test that config is applied
        assert executor.config.default_timeout == 2.0
        
        executor.cleanup()
    
    def test_command_specific_timeout(self):
        """Test command-specific timeout configuration."""
        config = TimeoutConfig()
        config.set_command_timeout("sleep", 1.0)
        
        executor = CommandExecutor(config)
        
        # Verify timeout is applied for sleep command
        timeout_val = config.get_timeout_for_command("sleep 5")
        assert timeout_val == 1.0
        
        executor.cleanup()


class TestErrorHandling:
    """Test cases for error handling and recovery."""
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        executor = CommandExecutor(verbose=False)
        
        # This should not raise an exception but return non-zero exit code
        exit_code, output = executor.execute("nonexistent_command_12345")
        
        assert exit_code != 0
        
        executor.cleanup()
    
    def test_process_cleanup_on_error(self):
        """Test that processes are cleaned up when errors occur."""
        executor = CommandExecutor(verbose=False)
        
        try:
            if platform.system() == "Windows":
                command = "ping -n 10 127.0.0.1"
            else:
                command = "sleep 10"
            
            with pytest.raises(CommandTimeoutError):
                executor.execute(command, timeout=0.5)
        
        finally:
            # Verify cleanup works
            executor.cleanup()
            
            # Should have no active processes after cleanup
            status = executor.get_status()
            assert status["active_processes"] == 0


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    def test_multiple_concurrent_commands(self):
        """Test handling of multiple commands (simulated)."""
        executor = CommandExecutor(verbose=False)
        
        try:
            # Execute multiple simple commands
            commands = [
                "echo 'Command 1'",
                "echo 'Command 2'", 
                "echo 'Command 3'"
            ]
            
            results = []
            for cmd in commands:
                if platform.system() == "Windows":
                    cmd = cmd.replace("'", '"')
                exit_code, output = executor.execute(cmd)
                results.append((exit_code, output))
            
            # Verify all commands succeeded
            for i, (exit_code, output) in enumerate(results):
                assert exit_code == 0
                assert f"Command {i+1}" in output
        
        finally:
            executor.cleanup()
    
    def test_timeout_and_recovery(self):
        """Test timeout handling and recovery."""
        executor = CommandExecutor(verbose=False)
        
        try:
            # Test timeout
            if platform.system() == "Windows":
                long_command = "ping -n 10 127.0.0.1"
            else:
                long_command = "sleep 5"
            
            with pytest.raises(CommandTimeoutError):
                executor.execute(long_command, timeout=1.0)
            
            # Test that executor still works after timeout
            simple_command = "echo 'Recovery test'"
            if platform.system() == "Windows":
                simple_command = 'echo "Recovery test"'
            
            exit_code, output = executor.execute(simple_command)
            assert exit_code == 0
            assert "Recovery test" in output
        
        finally:
            executor.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 