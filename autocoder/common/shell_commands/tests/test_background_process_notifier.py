"""
Tests for BackgroundProcessNotifier module.

This module provides comprehensive tests for the BackgroundProcessNotifier
class including process registration, monitoring, message handling,
and integration with the global process manager.
"""

import unittest
import pytest
import time
import threading
import tempfile
import os
import uuid
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from collections import deque

from autocoder.common.shell_commands.background_process_notifier import (
    BackgroundProcessNotifier,
    BackgroundTaskRegistration,
    AsyncTaskMessage,
    get_background_process_notifier
)
from autocoder.common.shell_commands import (
    execute_command_background,
)


def _indent_tail(text: str) -> str:
    """Helper function to indent text output."""
    return "\n".join(["    " + line for line in text.splitlines()])


class TestBackgroundTaskRegistration(unittest.TestCase):
    """Test BackgroundTaskRegistration dataclass."""
    
    def test_basic_creation(self):
        """Test basic registration creation."""
        registration = BackgroundTaskRegistration(
            conversation_id="conv_123",
            pid=1234,
            tool_name="execute_command",
            command="echo test",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task",
            task_id="task_123",
            start_time=time.time()
        )
        
        self.assertEqual(registration.conversation_id, "conv_123")
        self.assertEqual(registration.pid, 1234)
        self.assertEqual(registration.tool_name, "execute_command")
        self.assertEqual(registration.command, "echo test")
        self.assertEqual(registration.cwd, "/tmp")
        self.assertEqual(registration.agent_name, "test_agent")
        self.assertEqual(registration.task, "Test task")
        self.assertEqual(registration.task_id, "task_123")
        self.assertIsInstance(registration.start_time, float)


class TestAsyncTaskMessage(unittest.TestCase):
    """Test AsyncTaskMessage dataclass."""
    
    def test_basic_creation(self):
        """Test basic message creation."""
        message = AsyncTaskMessage(
            conversation_id="conv_123",
            task_id="task_123",
            pid=1234,
            tool_name="execute_command",
            status="completed",
            exit_code=0,
            duration_sec=5.5,
            command="echo test",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task",
            output_tail="Test output",
            error_tail=None,
            completed_at=time.time()
        )
        
        self.assertEqual(message.conversation_id, "conv_123")
        self.assertEqual(message.task_id, "task_123")
        self.assertEqual(message.pid, 1234)
        self.assertEqual(message.tool_name, "execute_command")
        self.assertEqual(message.status, "completed")
        self.assertEqual(message.exit_code, 0)
        self.assertEqual(message.duration_sec, 5.5)
        self.assertEqual(message.command, "echo test")
        self.assertEqual(message.cwd, "/tmp")
        self.assertEqual(message.agent_name, "test_agent")
        self.assertEqual(message.task, "Test task")
        self.assertEqual(message.output_tail, "Test output")
        self.assertIsNone(message.error_tail)
        self.assertIsInstance(message.completed_at, float)
        
    def test_failed_message(self):
        """Test message for failed task."""
        message = AsyncTaskMessage(
            conversation_id="conv_123",
            task_id="task_123",
            pid=1234,
            tool_name="execute_command",
            status="failed",
            exit_code=1,
            duration_sec=2.0,
            command="false",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task",
            output_tail="",
            error_tail="Command failed",
            completed_at=time.time()
        )
        
        self.assertEqual(message.status, "failed")
        self.assertEqual(message.exit_code, 1)
        self.assertEqual(message.error_tail, "Command failed")


class TestBackgroundProcessNotifier(unittest.TestCase):
    """Test BackgroundProcessNotifier main functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset singleton instance for clean testing
        BackgroundProcessNotifier._instance = None
        self.notifier = BackgroundProcessNotifier()
        
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.notifier.stop()
        except:
            pass
        # Reset singleton
        BackgroundProcessNotifier._instance = None
        
    def test_singleton_pattern(self):
        """Test that notifier follows singleton pattern."""
        notifier1 = BackgroundProcessNotifier.get_instance()
        notifier2 = BackgroundProcessNotifier.get_instance()
        self.assertIs(notifier1, notifier2)
        
    def test_initialization(self):
        """Test notifier initialization."""
        self.assertIsInstance(self.notifier._registrations, dict)
        self.assertIsInstance(self.notifier._pid_to_key, dict)
        self.assertIsInstance(self.notifier._reported, set)
        self.assertIsInstance(self.notifier._pending_messages, dict)
        self.assertEqual(self.notifier._poll_interval_sec, 0.5)
        self.assertEqual(self.notifier._max_output_bytes, 16 * 1024)
        self.assertEqual(self.notifier._max_output_lines, 200)
        
    def test_set_options(self):
        """Test setting notifier options."""
        self.notifier.set_options(
            poll_interval_sec=1.0,
            max_output_bytes=32 * 1024,
            max_output_lines=500
        )
        
        self.assertEqual(self.notifier._poll_interval_sec, 1.0)
        self.assertEqual(self.notifier._max_output_bytes, 32 * 1024)
        self.assertEqual(self.notifier._max_output_lines, 500)
        
    def test_set_options_invalid_values(self):
        """Test setting invalid options (should be ignored)."""
        original_interval = self.notifier._poll_interval_sec
        original_bytes = self.notifier._max_output_bytes
        original_lines = self.notifier._max_output_lines
        
        # Invalid values should be ignored
        self.notifier.set_options(
            poll_interval_sec=-1.0,
            max_output_bytes=-1,
            max_output_lines=-1
        )
        
        # Values should remain unchanged
        self.assertEqual(self.notifier._poll_interval_sec, original_interval)
        self.assertEqual(self.notifier._max_output_bytes, original_bytes)
        self.assertEqual(self.notifier._max_output_lines, original_lines)
        
    @patch('autocoder.common.shell_commands.background_process_notifier.get_background_process_info')
    def test_register_process(self, mock_get_info):
        """Test process registration."""
        # Mock process info
        mock_get_info.return_value = {"start_time": time.time()}
        
        task_id = self.notifier.register_process(
            conversation_id="conv_123",
            pid=1234,
            tool_name="execute_command",
            command="echo test",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task"
        )
        
        # Verify task_id is returned
        self.assertIsInstance(task_id, str)
        self.assertTrue(len(task_id) > 0)
        
        # Verify registration is stored
        with self.notifier._lock:
            self.assertTrue(len(self.notifier._registrations) > 0)
            self.assertIn(1234, self.notifier._pid_to_key)
            
        # Verify registration content
        key = self.notifier._pid_to_key[1234]
        registration = self.notifier._registrations[key]
        self.assertEqual(registration.conversation_id, "conv_123")
        self.assertEqual(registration.pid, 1234)
        self.assertEqual(registration.tool_name, "execute_command")
        self.assertEqual(registration.command, "echo test")
        self.assertEqual(registration.task_id, task_id)
        
    def test_poll_messages_empty(self):
        """Test polling messages from empty conversation."""
        messages = self.notifier.poll_messages("nonexistent_conv")
        self.assertEqual(messages, [])
        
    def test_poll_messages_with_content(self):
        """Test polling messages with content."""
        # Add some test messages
        test_message = AsyncTaskMessage(
            conversation_id="conv_123",
            task_id="task_123",
            pid=1234,
            tool_name="execute_command",
            status="completed",
            exit_code=0,
            duration_sec=1.0,
            command="echo test",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task",
            output_tail="test output",
            error_tail=None,
            completed_at=time.time()
        )
        
        with self.notifier._lock:
            self.notifier._pending_messages["conv_123"].append(test_message)
            
        # Poll messages
        messages = self.notifier.poll_messages("conv_123")
        
        # Verify message is returned and removed from queue
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].task_id, "task_123")
        
        # Verify queue is now empty
        with self.notifier._lock:
            self.assertNotIn("conv_123", self.notifier._pending_messages)
            
    def test_poll_messages_with_limit(self):
        """Test polling messages with max_items limit."""
        # Add multiple test messages
        for i in range(5):
            test_message = AsyncTaskMessage(
                conversation_id="conv_123",
                task_id=f"task_{i}",
                pid=1234 + i,
                tool_name="execute_command",
                status="completed",
                exit_code=0,
                duration_sec=1.0,
                command=f"echo test{i}",
                cwd="/tmp",
                agent_name="test_agent",
                task=f"Test task {i}",
                output_tail=f"test output {i}",
                error_tail=None,
                completed_at=time.time()
            )
            
            with self.notifier._lock:
                self.notifier._pending_messages["conv_123"].append(test_message)
                
        # Poll with limit
        messages = self.notifier.poll_messages("conv_123", max_items=3)
        
        # Verify only 3 messages returned
        self.assertEqual(len(messages), 3)
        
        # Verify remaining messages still in queue
        with self.notifier._lock:
            remaining = len(self.notifier._pending_messages["conv_123"])
            self.assertEqual(remaining, 2)
            
    def test_has_messages(self):
        """Test checking for pending messages."""
        # Initially no messages
        self.assertFalse(self.notifier.has_messages("conv_123"))
        
        # Add a message
        test_message = AsyncTaskMessage(
            conversation_id="conv_123",
            task_id="task_123",
            pid=1234,
            tool_name="execute_command",
            status="completed",
            exit_code=0,
            duration_sec=1.0,
            command="echo test",
            cwd="/tmp",
            agent_name="test_agent",
            task="Test task",
            output_tail="test output",
            error_tail=None,
            completed_at=time.time()
        )
        
        with self.notifier._lock:
            self.notifier._pending_messages["conv_123"].append(test_message)
            
        # Now should have messages
        self.assertTrue(self.notifier.has_messages("conv_123"))
        
        # Poll messages to empty queue
        self.notifier.poll_messages("conv_123")
        
        # Should no longer have messages
        self.assertFalse(self.notifier.has_messages("conv_123"))
        
    def test_stop(self):
        """Test stopping the notifier."""
        # Notifier should be running initially
        self.assertTrue(self.notifier._monitor_thread.is_alive())
        
        # Stop notifier
        self.notifier.stop()
        
        # Give some time for thread to stop
        time.sleep(0.1)
        
        # Monitor thread should be stopped
        self.assertFalse(self.notifier._monitor_thread.is_alive())


class TestBackgroundProcessNotifierFileOperations(unittest.TestCase):
    """Test file operations for background process notifier."""
    
    def setUp(self):
        """Set up test environment with temp directory."""
        BackgroundProcessNotifier._instance = None
        self.notifier = BackgroundProcessNotifier()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        try:
            self.notifier.stop()
        except:
            pass
        BackgroundProcessNotifier._instance = None
        
        # Clean up temp directory
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    def test_read_file_tail_nonexistent(self):
        """Test reading tail of non-existent file."""
        result = self.notifier._read_file_tail("/nonexistent/file.txt")
        self.assertIsNone(result)
        
    def test_read_file_tail_empty(self):
        """Test reading tail of empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
            
        result = self.notifier._read_file_tail(empty_file)
        self.assertEqual(result, "")
        
    def test_read_file_tail_small_file(self):
        """Test reading tail of small file."""
        small_file = os.path.join(self.temp_dir, "small.txt")
        content = "Line 1\nLine 2\nLine 3\n"
        
        with open(small_file, 'w') as f:
            f.write(content)
            
        result = self.notifier._read_file_tail(small_file)
        self.assertEqual(result, content.strip())
        
    def test_read_file_tail_large_file(self):
        """Test reading tail of large file with size limit."""
        large_file = os.path.join(self.temp_dir, "large.txt")
        
        # Create file larger than max_output_bytes
        lines = [f"Line {i}\n" for i in range(1000)]
        content = "".join(lines)
        
        with open(large_file, 'w') as f:
            f.write(content)
            
        # Set small limit for testing
        self.notifier._max_output_bytes = 100
        self.notifier._max_output_lines = 10
        
        result = self.notifier._read_file_tail(large_file)
        
        # Should be truncated
        self.assertLess(len(result), len(content))
        self.assertLessEqual(len(result.split('\n')), 10)
        
    def test_tail_text_line_limit(self):
        """Test text tailing with line limit."""
        text = "\n".join([f"Line {i}" for i in range(50)])
        
        # Set line limit
        self.notifier._max_output_lines = 10
        
        result = self.notifier._tail_text(text)
        lines = result.split('\n')
        
        self.assertLessEqual(len(lines), 10)
        self.assertTrue(result.endswith("Line 49"))  # Should end with last line
        
    def test_tail_text_byte_limit(self):
        """Test text tailing with byte limit."""
        text = "A" * 1000  # 1000 character string
        
        # Set small byte limit
        self.notifier._max_output_bytes = 100
        
        result = self.notifier._tail_text(text)
        
        # Should be truncated to approximately byte limit
        self.assertLessEqual(len(result.encode('utf-8')), self.notifier._max_output_bytes + 10)  # Small tolerance
        
    def test_read_process_output_tails_success(self):
        """Test reading process output tails successfully."""
        # Create test output files
        pid = 12345
        process_uniq_id = "test_proc_123"
        backgrounds_dir = os.path.join(self.temp_dir, '.auto-coder', 'backgrounds')
        os.makedirs(backgrounds_dir, exist_ok=True)
        
        stdout_file = os.path.join(backgrounds_dir, f"{process_uniq_id}.out")
        stderr_file = os.path.join(backgrounds_dir, f"{process_uniq_id}.err")
        
        # Create test files
        with open(stdout_file, 'w') as f:
            f.write("Standard output content")
        with open(stderr_file, 'w') as f:
            f.write("Standard error content")
            
        # Test reading
        info = {
            "pid": pid,
            "process_uniq_id": process_uniq_id,
            "cwd": self.temp_dir
        }
        
        stdout_tail, stderr_tail = self.notifier._read_process_output_tails(info)
        
        self.assertEqual(stdout_tail, "Standard output content")
        self.assertEqual(stderr_tail, "Standard error content")
        
    def test_read_process_output_tails_missing_process_uniq_id(self):
        """Test reading process output tails without process_uniq_id."""
        info = {
            "pid": 12345,
            "cwd": self.temp_dir
        }
        
        stdout_tail, stderr_tail = self.notifier._read_process_output_tails(info)
        
        # Should return None for both since process_uniq_id is required
        self.assertIsNone(stdout_tail)
        self.assertIsNone(stderr_tail)


class TestBackgroundProcessNotifierIntegration(unittest.TestCase):
    """Integration tests for BackgroundProcessNotifier."""
    
    def setUp(self):
        """Set up integration test environment."""
        BackgroundProcessNotifier._instance = None
        self.notifier = BackgroundProcessNotifier()
        
    def tearDown(self):
        """Clean up integration tests."""
        try:
            self.notifier.stop()
        except:
            pass
        BackgroundProcessNotifier._instance = None
        
    @patch('autocoder.common.shell_commands.background_process_notifier.get_background_processes')
    @patch('autocoder.common.shell_commands.background_process_notifier.get_background_process_info')
    def test_scan_background_processes_completion(self, mock_get_info, mock_get_processes):
        """Test scanning for process completion."""
        # Setup mocks
        start_time = time.time()
        end_time = start_time + 5.0
        
        mock_get_processes.return_value = {
            1234: {
                "pid": 1234,
                "process_uniq_id": "test_proc_123",
                "status": "completed",
                "exit_code": 0,
                "start_time": start_time,
                "end_time": end_time,
                "cwd": "/tmp"
            }
        }
        
        mock_get_info.return_value = {
            "start_time": start_time
        }
        
        # Register a process
        task_id = self.notifier.register_process(
            conversation_id="conv_123",
            pid=1234,
            tool_name="execute_command",
            command="echo test",
            cwd="/tmp"
        )
        
        # Manually trigger scan
        self.notifier._scan_background_processes()
        
        # Check for completion message
        messages = self.notifier.poll_messages("conv_123")
        
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.task_id, task_id)
        self.assertEqual(message.status, "completed")
        self.assertEqual(message.exit_code, 0)
        self.assertEqual(message.pid, 1234)
        
    @patch('autocoder.common.shell_commands.background_process_notifier.get_background_processes')
    @patch('autocoder.common.shell_commands.background_process_notifier.get_background_process_info')
    def test_scan_background_processes_failure(self, mock_get_info, mock_get_processes):
        """Test scanning for process failure."""
        # Setup mocks for failed process
        start_time = time.time()
        end_time = start_time + 2.0
        
        mock_get_processes.return_value = {
            1234: {
                "pid": 1234,
                "process_uniq_id": "test_proc_123",
                "status": "completed",
                "exit_code": 1,  # Failed
                "start_time": start_time,
                "end_time": end_time,
                "cwd": "/tmp"
            }
        }
        
        mock_get_info.return_value = {
            "start_time": start_time
        }
        
        # Register a process
        task_id = self.notifier.register_process(
            conversation_id="conv_123",
            pid=1234,
            tool_name="execute_command",
            command="false",  # Command that fails
            cwd="/tmp"
        )
        
        # Manually trigger scan
        self.notifier._scan_background_processes()
        
        # Check for failure message
        messages = self.notifier.poll_messages("conv_123")
        
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.task_id, task_id)
        self.assertEqual(message.status, "failed")
        self.assertEqual(message.exit_code, 1)
        
    def test_get_process_start_time_with_info(self):
        """Test getting process start time when info is available."""
        with patch('autocoder.common.shell_commands.background_process_notifier.get_background_process_info') as mock_get_info:
            mock_get_info.return_value = {"start_time": 123456.789}
            
            start_time = self.notifier._get_process_start_time(1234)
            self.assertEqual(start_time, 123456.789)
            
    def test_get_process_start_time_without_info(self):
        """Test getting process start time when info is not available."""
        with patch('autocoder.common.shell_commands.background_process_notifier.get_background_process_info') as mock_get_info:
            mock_get_info.return_value = None
            
            before_time = time.time()
            start_time = self.notifier._get_process_start_time(1234)
            after_time = time.time()
            
            # Should return current time
            self.assertGreaterEqual(start_time, before_time)
            self.assertLessEqual(start_time, after_time)


class TestGetBackgroundProcessNotifier(unittest.TestCase):
    """Test the get_background_process_notifier convenience function."""
    
    def setUp(self):
        """Reset singleton for testing."""
        BackgroundProcessNotifier._instance = None
        
    def tearDown(self):
        """Clean up singleton."""
        if BackgroundProcessNotifier._instance:
            try:
                BackgroundProcessNotifier._instance.stop()
            except:
                pass
        BackgroundProcessNotifier._instance = None
        
    def test_get_background_process_notifier(self):
        """Test that function returns singleton instance."""
        notifier1 = get_background_process_notifier()
        notifier2 = get_background_process_notifier()
        
        self.assertIs(notifier1, notifier2)
        self.assertIsInstance(notifier1, BackgroundProcessNotifier)


def test_background_process_notifier_basic():
    """
    Start a short-lived background command, register it to BackgroundProcessNotifier,
    poll for completion, print a summary (similar to AgenticEdit) and assert results.
    """
    # Unique conversation id to scope messages
    conv_id = f"test-conv-{uuid.uuid4()}"

    # Short-lived command that prints output and exits with code 0
    # Use Python to ensure cross-platform behavior
    command = 'python -c "import time,sys; print(\\"start\\"); sys.stdout.flush(); time.sleep(0.6); print(\\"end\\")"'

    # Start background process
    info = execute_command_background(command=command, verbose=True)

    # Register with notifier
    notifier = get_background_process_notifier()
    notifier.set_options(poll_interval_sec=0.1, max_output_bytes=4096, max_output_lines=50)
    notifier.register_process(
        conversation_id=conv_id,
        pid=info["pid"],
        tool_name="ExecuteCommandTool",
        command=info["command"],
        cwd=info.get("working_directory"),
    )

    # Poll for completion with timeout
    deadline = time.time() + 10.0
    while time.time() < deadline and not notifier.has_messages(conv_id):
        time.sleep(0.1)

    msgs = notifier.poll_messages(conv_id, max_items=16)

    # Print summary similar to AgenticEdit injection
    print(f"后台任务完成通知（{len(msgs)} 项）：")
    for m in msgs:
        meta = []
        if m.exit_code is not None:
            meta.append(f"exit_code={m.exit_code}")
        if m.duration_sec is not None:
            meta.append(f"duration={m.duration_sec:.2f}s")
        meta_str = ", ".join(meta)
        print(f"- [{m.tool_name}] pid={m.pid} status={m.status} {('('+meta_str+')') if meta_str else ''}")
        if m.agent_name or m.task:
            detail = []
            if m.agent_name:
                detail.append(f"agent={m.agent_name}")
            if m.task:
                detail.append(f"task={m.task}")
            print("  " + ", ".join(detail))
        if m.output_tail:
            print("  output_tail:\n" + _indent_tail(m.output_tail))
        if m.error_tail:
            print("  error_tail:\n" + _indent_tail(m.error_tail))

    # Basic assertions
    assert len(msgs) >= 1, "expected at least one completion message"
    m0 = msgs[0]
    assert m0.conversation_id == conv_id
    assert m0.pid == info["pid"]
    assert m0.status in ("completed", "failed")


if __name__ == "__main__":
    unittest.main()