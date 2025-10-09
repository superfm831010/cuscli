"""
Tests for batch command execution functionality.

This module tests the execute_commands and execute_batch functions
for both parallel and serial execution modes.
"""

import pytest
import time
import platform
from typing import List, Dict, Any
import json

from ..command_executor import CommandExecutor, execute_commands
from ..timeout_config import TimeoutConfig
from ..exceptions import CommandTimeoutError, CommandExecutionError


class TestExecuteBatch:
    """Test cases for execute_batch method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TimeoutConfig(default_timeout=10.0)
        self.executor = CommandExecutor(self.config, verbose=False)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.executor.cleanup()
    
    def test_empty_commands_list(self):
        """Test execution with empty commands list."""
        results = self.executor.execute_batch([])
        assert results == []
    
    def test_single_command_serial(self):
        """Test executing a single command serially."""
        if platform.system() == "Windows":
            commands = ["echo Hello"]
        else:
            commands = ["echo 'Hello'"]
        
        results = self.executor.execute_batch(commands, parallel=False)
        
        assert len(results) == 1
        assert results[0]["index"] == 0
        assert results[0]["exit_code"] == 0
        assert "Hello" in results[0]["output"]
        assert results[0]["timed_out"] is False
    
    def test_multiple_commands_serial(self):
        """Test executing multiple commands serially."""
        if platform.system() == "Windows":
            commands = ["echo One", "echo Two", "echo Three"]
        else:
            commands = ["echo 'One'", "echo 'Two'", "echo 'Three'"]
        
        start_time = time.time()
        results = self.executor.execute_batch(commands, parallel=False)
        duration = time.time() - start_time
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["index"] == i
            assert result["exit_code"] == 0
            assert result["timed_out"] is False
        
        assert "One" in results[0]["output"]
        assert "Two" in results[1]["output"]
        assert "Three" in results[2]["output"]
    
    def test_multiple_commands_parallel(self):
        """Test executing multiple commands in parallel."""
        if platform.system() == "Windows":
            commands = ["echo Alpha", "echo Beta", "echo Gamma"]
        else:
            commands = ["echo 'Alpha'", "echo 'Beta'", "echo 'Gamma'"]
        
        start_time = time.time()
        results = self.executor.execute_batch(commands, parallel=True)
        duration = time.time() - start_time
        
        assert len(results) == 3
        
        # Results should maintain order even when executed in parallel
        assert results[0]["index"] == 0
        assert results[1]["index"] == 1
        assert results[2]["index"] == 2
        
        assert "Alpha" in results[0]["output"]
        assert "Beta" in results[1]["output"]
        assert "Gamma" in results[2]["output"]
    
    def test_command_failure_serial(self):
        """Test handling of failed commands in serial execution."""
        if platform.system() == "Windows":
            commands = ["echo Success", "exit 1", "echo After"]
        else:
            commands = ["echo Success", "false", "echo After"]
        
        results = self.executor.execute_batch(commands, parallel=False)
        
        assert len(results) == 3
        assert results[0]["exit_code"] == 0
        assert results[1]["exit_code"] != 0
        assert results[2]["exit_code"] == 0  # Should continue after failure
    
    def test_command_failure_parallel(self):
        """Test handling of failed commands in parallel execution."""
        if platform.system() == "Windows":
            commands = ["echo OK1", "exit 1", "echo OK2"]
        else:
            commands = ["echo OK1", "false", "echo OK2"]
        
        results = self.executor.execute_batch(commands, parallel=True)
        
        assert len(results) == 3
        assert results[0]["exit_code"] == 0
        assert results[1]["exit_code"] != 0
        assert results[2]["exit_code"] == 0
    
    def test_per_command_timeout(self):
        """Test per-command timeout in serial execution."""
        if platform.system() == "Windows":
            commands = ["echo Quick", "ping -n 10 127.0.0.1", "echo Done"]
        else:
            commands = ["echo Quick", "sleep 10", "echo Done"]
        
        results = self.executor.execute_batch(
            commands,
            per_command_timeout=0.5,
            parallel=False
        )
        
        assert len(results) == 3
        assert results[0]["exit_code"] == 0
        assert results[0]["timed_out"] is False
        
        assert results[1]["exit_code"] == -1
        assert results[1]["timed_out"] is True
        assert "timed out" in results[1]["error"].lower()
        
        # Should continue after timeout
        assert results[2]["exit_code"] == 0
        assert results[2]["timed_out"] is False
    
    def test_overall_timeout_serial(self):
        """Test overall timeout in serial execution."""
        if platform.system() == "Windows":
            commands = ["ping -n 2 127.0.0.1"] * 5
        else:
            commands = ["sleep 1"] * 5
        
        start_time = time.time()
        results = self.executor.execute_batch(
            commands,
            timeout=2.0,  # Overall timeout shorter than total execution
            parallel=False
        )
        duration = time.time() - start_time
        
        assert duration < 3.0  # Should timeout before all complete
        
        # Some commands should have executed
        executed_count = sum(1 for r in results if not r["timed_out"])
        timed_out_count = sum(1 for r in results if r["timed_out"])
        
        assert executed_count > 0
        assert timed_out_count > 0
        assert len(results) == 5
    
    def test_overall_timeout_parallel(self):
        """Test overall timeout in parallel execution."""
        if platform.system() == "Windows":
            commands = ["ping -n 5 127.0.0.1"] * 4
        else:
            commands = ["sleep 3"] * 4
        
        start_time = time.time()
        results = self.executor.execute_batch(
            commands,
            timeout=1.0,  # Overall timeout
            parallel=True
        )
        duration = time.time() - start_time
        
        assert duration < 3.0  # Should timeout quickly (allowing for cleanup time)
        assert len(results) == 4
        
        # All should timeout since they're running in parallel
        for result in results:
            assert result["timed_out"] is True
    
    def test_mixed_success_and_failure(self):
        """Test batch with mix of successful and failing commands."""
        if platform.system() == "Windows":
            commands = [
                "echo Start",
                "exit 0",
                "exit 1",
                "ping -n 10 127.0.0.1",  # Will timeout
                "echo End"
            ]
        else:
            commands = [
                "echo Start",
                "true",
                "false", 
                "sleep 10",  # Will timeout
                "echo End"
            ]
        
        results = self.executor.execute_batch(
            commands,
            per_command_timeout=0.5,
            parallel=False
        )
        
        assert len(results) == 5
        assert results[0]["exit_code"] == 0  # echo Start
        assert results[1]["exit_code"] == 0  # exit 0 / true
        assert results[2]["exit_code"] != 0  # exit 1 / false
        assert results[3]["timed_out"] is True  # timeout
        assert results[4]["exit_code"] == 0  # echo End
    
    def test_result_structure(self):
        """Test that results have the expected structure."""
        commands = ["echo Test"]
        results = self.executor.execute_batch(commands)
        
        assert len(results) == 1
        result = results[0]
        
        # Check all expected fields
        assert "command" in result
        assert "index" in result
        assert "exit_code" in result
        assert "output" in result
        assert "error" in result
        assert "timed_out" in result
        assert "duration" in result
        assert "start_time" in result
        assert "end_time" in result
        
        # Check types
        assert isinstance(result["command"], str)
        assert isinstance(result["index"], int)
        assert isinstance(result["exit_code"], int)
        assert isinstance(result["output"], str)
        assert result["error"] is None or isinstance(result["error"], str)
        assert isinstance(result["timed_out"], bool)
        assert isinstance(result["duration"], float)
        assert isinstance(result["start_time"], float)
        assert isinstance(result["end_time"], float)
    
    def test_command_ordering_preserved(self):
        """Test that command order is preserved in results."""
        commands = [f"echo 'Command {i}'" for i in range(10)]
        
        # Test both serial and parallel
        for parallel in [False, True]:
            results = self.executor.execute_batch(commands, parallel=parallel)
            
            assert len(results) == 10
            for i, result in enumerate(results):
                assert result["index"] == i
                assert f"Command {i}" in result["output"]


class TestExecuteCommands:
    """Test cases for the convenience execute_commands function."""
    
    def test_basic_parallel_execution(self):
        """Test basic parallel execution with convenience function."""
        if platform.system() == "Windows":
            commands = ["echo A", "echo B", "echo C"]
        else:
            commands = ["echo A", "echo B", "echo C"]
        
        results = execute_commands(commands, parallel=True)
        
        assert len(results) == 3
        assert all(r["exit_code"] == 0 for r in results)
        assert "A" in results[0]["output"]
        assert "B" in results[1]["output"]
        assert "C" in results[2]["output"]
    
    def test_basic_serial_execution(self):
        """Test basic serial execution with convenience function."""
        commands = ["echo 1", "echo 2", "echo 3"]
        
        results = execute_commands(commands, parallel=False)
        
        assert len(results) == 3
        assert all(r["exit_code"] == 0 for r in results)
    
    def test_with_timeout_options(self):
        """Test convenience function with timeout options."""
        if platform.system() == "Windows":
            commands = ["echo Fast", "ping -n 5 127.0.0.1"]
        else:
            commands = ["echo Fast", "sleep 3"]
        
        results = execute_commands(
            commands,
            per_command_timeout=1.0,
            parallel=False
        )
        
        assert results[0]["timed_out"] is False
        assert results[1]["timed_out"] is True
    
    def test_with_working_directory(self):
        """Test execution with custom working directory."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file in temp directory
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")
            
            if platform.system() == "Windows":
                commands = ["dir", "type test.txt"]
            else:
                commands = ["ls", "cat test.txt"]
            
            results = execute_commands(commands, cwd=temp_dir, parallel=False)
            
            assert all(r["exit_code"] == 0 for r in results)
            assert "test.txt" in results[0]["output"]
            assert "test content" in results[1]["output"]
    
    def test_empty_commands(self):
        """Test with empty command list."""
        results = execute_commands([])
        assert results == []
    
    def test_verbose_mode(self):
        """Test verbose mode doesn't break functionality."""
        commands = ["echo Verbose"]
        results = execute_commands(commands, verbose=True)
        
        assert len(results) == 1
        assert results[0]["exit_code"] == 0


class TestBatchExecutionEdgeCases:
    """Test edge cases for batch execution."""
    
    def test_very_large_batch(self):
        """Test execution of a large number of commands."""
        # Create 50 simple commands
        commands = [f"echo 'Item {i}'" for i in range(50)]
        
        results = execute_commands(commands, parallel=True)
        
        assert len(results) == 50
        assert all(r["exit_code"] == 0 for r in results)
    
    def test_invalid_commands(self):
        """Test batch with invalid commands."""
        commands = [
            "echo Valid",
            "this_command_does_not_exist_12345",
            "echo Also Valid"
        ]
        
        results = execute_commands(commands, parallel=False)
        
        assert len(results) == 3
        assert results[0]["exit_code"] == 0
        assert results[1]["exit_code"] != 0
        assert results[2]["exit_code"] == 0
    
    def test_mixed_command_types(self):
        """Test batch with different command formats."""
        commands = [
            "echo String command",
            ["echo", "List", "command"],
            "echo Another string"
        ]
        
        results = execute_commands(commands, parallel=False)
        
        assert len(results) == 3
        assert all(r["exit_code"] == 0 for r in results)
        assert "String command" in results[0]["output"]
        assert "List command" in results[1]["output"]
        assert "Another string" in results[2]["output"]


class TestExecuteBatchViaResolver:
    """Test cases for batch execution via ExecuteCommandToolResolver."""
    
    def test_json_array_batch(self):
        """Test batch execution using JSON array format."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        # Create tool with JSON array
        tool = ExecuteCommandTool(
            command='["echo Hello", "echo World", "echo Done"]',
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        assert result.success is True
        assert 'batch_results' in result.content
        assert len(result.content['batch_results']) == 3
        assert all(r['exit_code'] == 0 for r in result.content['batch_results'])
    
    def test_yaml_serial_mode(self):
        """Test batch execution using YAML format with serial mode."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        yaml_command = """mode: serial
cmds:
  - echo "Step 1"
  - echo "Step 2"
  - echo "Step 3"
"""
        
        tool = ExecuteCommandTool(
            command=yaml_command,
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        assert result.success is True
        assert result.content['summary']['execution_mode'] == 'serial'
        assert result.content['summary']['total'] == 3
    
    def test_newline_separated_batch(self):
        """Test batch execution using newline-separated format."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        commands = """echo "Line 1"
echo "Line 2"
echo "Line 3"
"""
        
        tool = ExecuteCommandTool(
            command=commands,
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        assert result.success is True
        # In newline separated mode, it's treated as single command output
        if isinstance(result.content, str):
            # Single command output
            assert "Line 1" in result.content
            assert "Line 2" in result.content  
            assert "Line 3" in result.content
        else:
            # Batch mode
            assert 'batch_results' in result.content
            assert len(result.content['batch_results']) == 3
    
    def test_single_command_fallback(self):
        """Test that single commands still work normally."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        tool = ExecuteCommandTool(
            command='echo "Single command"',
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        assert result.success is True
        # Single command should not have batch_results
        assert 'batch_results' not in result.content or result.content is None or isinstance(result.content, str)
    
    def test_serial_with_comment(self):
        """Test serial execution with comment prefix."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        commands = """# serial
echo "First"
echo "Second"
echo "Third"
"""
        
        tool = ExecuteCommandTool(
            command=commands,
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        assert result.success is True
        assert result.content['summary']['execution_mode'] == 'serial'
    
    def test_batch_with_failure(self):
        """Test batch execution with some commands failing."""
        from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
        from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
        from autocoder.common import AutoCoderArgs
        
        if platform.system() == "Windows":
            commands = ['echo "Success"', 'exit 1', 'echo "After failure"']
        else:
            commands = ['echo "Success"', 'false', 'echo "After failure"']
        
        tool = ExecuteCommandTool(
            command=json.dumps(commands),
            requires_approval=False,
            timeout=30
        )
        
        args = AutoCoderArgs(
            source_dir=".",
            enable_agentic_dangerous_command_check=False,
            enable_agentic_auto_approve=True,
            use_shell_commands=True
        )
        
        resolver = ExecuteCommandToolResolver(None, tool, args)
        result = resolver.resolve()
        
        # Overall result should be False due to failure
        assert result.success is False
        assert result.content['summary']['failed'] == 1
        assert result.content['summary']['successful'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 