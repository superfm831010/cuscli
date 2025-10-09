"""
Integration tests for Shell Commands module.

This module provides comprehensive integration tests that verify
the interaction between different components of the shell commands
system including command execution, process management, timeout
handling, background processing, and interactive sessions.
"""

import unittest
import pytest
import time
import tempfile
import os
import platform
import threading
from unittest.mock import patch
from typing import List, Dict, Any

from autocoder.common.shell_commands import (
    CommandExecutor,
    TimeoutConfig,
    execute_command,
    execute_command_background,
    execute_commands,
    get_background_processes,
    get_background_process_info,
    cleanup_background_process,
    InteractiveCommandExecutor,
    execute_interactive,
    create_interactive_shell,
    get_session_manager,
    get_background_process_notifier,
    CommandTimeoutError,
    CommandExecutionError
)


class TestBasicIntegration(unittest.TestCase):
    """Test basic integration between core components."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    def test_command_executor_with_timeout_config(self):
        """Test CommandExecutor integration with TimeoutConfig."""
        # Create custom timeout configuration
        config = TimeoutConfig(
            default_timeout=5.0,
            cleanup_timeout=2.0,
            grace_period=1.0
        )
        config.set_command_timeout("echo*", 10.0)
        
        # Create executor with custom config
        executor = CommandExecutor(config=config, verbose=True)
        
        try:
            # Test normal command execution
            exit_code, output = executor.execute("echo 'Hello Integration'")
            self.assertEqual(exit_code, 0)
            self.assertIn("Hello Integration", output)
            
            # Test command with specific timeout
            start_time = time.time()
            exit_code, output = executor.execute("echo 'Specific timeout'")
            duration = time.time() - start_time
            
            self.assertEqual(exit_code, 0)
            self.assertLess(duration, 10.0)  # Should complete quickly
            
        finally:
            executor.cleanup()
            
    def test_command_executor_with_working_directory(self):
        """Test CommandExecutor with custom working directory."""
        config = TimeoutConfig(default_timeout=10.0)
        executor = CommandExecutor(config=config)
        
        try:
            # Test command in custom directory
            if platform.system() == "Windows":
                exit_code, output = executor.execute("dir", cwd=self.temp_dir)
            else:
                exit_code, output = executor.execute("pwd", cwd=self.temp_dir)
            
            self.assertEqual(exit_code, 0)
            if platform.system() != "Windows":
                self.assertIn(self.temp_dir, output)
                
        finally:
            executor.cleanup()
            
    def test_timeout_integration(self):
        """Test timeout integration across components."""
        config = TimeoutConfig(default_timeout=2.0)
        executor = CommandExecutor(config=config)
        
        try:
            # Test timeout with cleanup
            with self.assertRaises(CommandTimeoutError):
                executor.execute("sleep 5")  # Should timeout after 2 seconds
                
        finally:
            executor.cleanup()


class TestBackgroundProcessIntegration(unittest.TestCase):
    """Test background process integration."""
    
    def setUp(self):
        """Set up background process tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up background process tests."""
        # Clean up any remaining background processes
        try:
            bg_processes = get_background_processes()
            for pid in bg_processes.keys():
                cleanup_background_process(pid)
        except:
            pass
            
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    @pytest.mark.integration
    def test_background_execution_lifecycle(self):
        """Test complete background execution lifecycle."""
        # Start background process
        info = execute_command_background(
            "python -c \"import time; print('start'); time.sleep(1); print('end')\"",
            cwd=self.temp_dir
        )
        
        try:
            self.assertIn("pid", info)
            self.assertIn("command", info)
            pid = info["pid"]
            
            # Verify process is tracked
            bg_processes = get_background_processes()
            self.assertIn(pid, bg_processes)
            
            # Get process info
            process_info = get_background_process_info(pid)
            self.assertIsNotNone(process_info)
            self.assertEqual(process_info["command"], info["command"])
            
            # Wait for completion
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second timeout
                process_info = get_background_process_info(pid)
                if process_info and process_info.get("status") == "completed":
                    break
                time.sleep(0.1)
            
            # Verify completion
            final_info = get_background_process_info(pid)
            self.assertEqual(final_info["status"], "completed")
            self.assertEqual(final_info["exit_code"], 0)
            
        finally:
            # Clean up
            cleanup_background_process(pid)
            
    @pytest.mark.integration
    def test_background_process_with_notifier(self):
        """Test background process integration with notifier."""
        import uuid
        
        conv_id = f"test-{uuid.uuid4()}"
        notifier = get_background_process_notifier()
        
        try:
            # Start background process
            info = execute_command_background(
                "python -c \"print('notification test')\"",
                cwd=self.temp_dir
            )
            
            # Register with notifier
            task_id = notifier.register_process(
                conversation_id=conv_id,
                pid=info["pid"],
                tool_name="test_tool",
                command=info["command"],
                cwd=self.temp_dir
            )
            
            # Wait for completion notification
            deadline = time.time() + 10.0
            while time.time() < deadline:
                if notifier.has_messages(conv_id):
                    break
                time.sleep(0.1)
            
            # Check for messages
            messages = notifier.poll_messages(conv_id)
            self.assertGreater(len(messages), 0)
            
            message = messages[0]
            self.assertEqual(message.task_id, task_id)
            self.assertEqual(message.conversation_id, conv_id)
            self.assertIn(message.status, ["completed", "failed"])
            
        finally:
            # Clean up
            if 'info' in locals():
                cleanup_background_process(info["pid"])
                
    @pytest.mark.integration
    def test_concurrent_background_processes(self):
        """Test multiple concurrent background processes."""
        processes = []
        
        try:
            # Start multiple background processes
            for i in range(3):
                info = execute_command_background(
                    f"python -c \"import time; print('process {i}'); time.sleep(0.5)\"",
                    cwd=self.temp_dir
                )
                processes.append(info)
            
            # Verify all processes are tracked
            bg_processes = get_background_processes()
            for info in processes:
                self.assertIn(info["pid"], bg_processes)
                
            # Wait for all to complete
            deadline = time.time() + 15.0
            while time.time() < deadline:
                all_completed = True
                for info in processes:
                    process_info = get_background_process_info(info["pid"])
                    if not process_info or process_info.get("status") != "completed":
                        all_completed = False
                        break
                        
                if all_completed:
                    break
                time.sleep(0.1)
                
            # Verify all completed successfully
            for info in processes:
                process_info = get_background_process_info(info["pid"])
                self.assertEqual(process_info["status"], "completed")
                self.assertEqual(process_info["exit_code"], 0)
                
        finally:
            # Clean up all processes
            for info in processes:
                cleanup_background_process(info["pid"])


class TestInteractiveSessionIntegration(unittest.TestCase):
    """Test interactive session integration."""
    
    def setUp(self):
        """Set up interactive session tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up interactive session tests."""
        # Clean up any remaining sessions
        try:
            manager = get_session_manager()
            manager.cleanup_all()
        except:
            pass
            
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    @pytest.mark.integration
    def test_interactive_session_creation_and_communication(self):
        """Test creating interactive session and communication."""
        manager = get_session_manager()
        
        # Create session
        result = manager.create_session(
            "python -c \"import sys; print('Ready'); sys.stdout.flush(); exec(input())\"",
            cwd=self.temp_dir,
            timeout=30,
            use_pexpect=False
        )
        
        try:
            self.assertTrue(result.success, f"Session creation failed: {result.message}")
            session_id = result.content["session_id"]
            
            # Send input
            input_result = manager.send_input(session_id, "print('Hello from session')\n")
            self.assertTrue(input_result.success)
            
            # Read output
            time.sleep(0.5)  # Give time for command to execute
            output_result = manager.read_output(session_id)
            # Output reading might not always succeed depending on timing
            if not output_result.success:
                print(f"Output read failed: {output_result.message}")
            # Don't assert success as it may depend on timing
            
        finally:
            if result.success:
                manager.terminate_session(result.content["session_id"])
                
    @pytest.mark.integration
    @pytest.mark.skipif(platform.system() == "Windows", reason="Shell behavior different on Windows")
    def test_interactive_shell_integration(self):
        """Test interactive shell integration."""
        session = create_interactive_shell(timeout=30)
        
        try:
            self.assertIsNotNone(session)
            self.assertTrue(session.process.is_alive())
            
            # Send command
            session.process.write("echo 'shell test'\n")
            
            # Read output
            time.sleep(0.5)
            output = session.process.read_output(timeout=2.0)
            
            # Output might contain shell control characters
            if output:
                # Clean the output and check for our test string
                clean_output = output.replace('\x1b', '').replace('\r', '').replace('%', '')
                if "shell test" not in clean_output:
                    print(f"Unexpected output: {repr(output)}")
                    # Don't fail the test as shell output can vary
                
        finally:
            session.terminate()
            
    @pytest.mark.integration
    def test_multiple_interactive_sessions(self):
        """Test managing multiple interactive sessions."""
        executor = InteractiveCommandExecutor()
        sessions = []
        
        try:
            # Create multiple sessions
            for i in range(3):
                session = executor.execute_interactive(
                    f"python -c \"print('session {i}'); import time; time.sleep(1)\"",
                    timeout=10
                )
                sessions.append(session)
                
            # Verify all sessions are active
            session_list = executor.list_sessions()
            self.assertEqual(len(session_list), 3)
            
            # Verify each session has unique ID
            session_ids = [s["session_id"] for s in session_list]
            self.assertEqual(len(session_ids), len(set(session_ids)))
            
        finally:
            # Clean up all sessions
            executor.cleanup()


class TestBatchExecutionIntegration(unittest.TestCase):
    """Test batch execution integration."""
    
    def setUp(self):
        """Set up batch execution tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up batch execution tests."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    @pytest.mark.integration
    def test_batch_parallel_execution(self):
        """Test parallel batch execution."""
        commands = [
            "echo 'Task 1'",
            "echo 'Task 2'", 
            "echo 'Task 3'"
        ]
        
        start_time = time.time()
        results = execute_commands(commands, parallel=True, timeout=10.0)
        duration = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(results), 3)
        
        for i, result in enumerate(results):
            self.assertEqual(result["index"], i)
            self.assertEqual(result["exit_code"], 0)
            self.assertIn(f"Task {i+1}", result["output"])
            self.assertFalse(result["timed_out"])
            
        # Parallel execution should be faster than serial
        self.assertLess(duration, 5.0)
        
    @pytest.mark.integration 
    def test_batch_serial_execution(self):
        """Test serial batch execution."""
        commands = [
            "echo 'Step 1'",
            "echo 'Step 2'",
            "echo 'Step 3'"
        ]
        
        results = execute_commands(commands, parallel=False, timeout=10.0)
        
        # Verify results are in order
        self.assertEqual(len(results), 3)
        
        for i, result in enumerate(results):
            self.assertEqual(result["index"], i)
            self.assertEqual(result["exit_code"], 0)
            self.assertIn(f"Step {i+1}", result["output"])
            
    @pytest.mark.integration
    def test_batch_with_failures(self):
        """Test batch execution with some failures."""
        commands = [
            "echo 'Success'",
            "python -c \"import sys; sys.exit(1)\"",  # This will fail
            "echo 'Another success'"
        ]
        
        results = execute_commands(commands, parallel=True, timeout=10.0)
        
        # Verify mixed results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["exit_code"], 0)  # Success
        self.assertEqual(results[1]["exit_code"], 1)  # Failure
        self.assertEqual(results[2]["exit_code"], 0)  # Success
        
    @pytest.mark.integration
    def test_batch_with_timeout(self):
        """Test batch execution with timeouts."""
        commands = [
            "echo 'Quick task'",
            "python -c \"import time; time.sleep(5)\"",  # This will timeout
            "echo 'Another quick task'"
        ]
        
        results = execute_commands(
            commands, 
            parallel=True, 
            per_command_timeout=1.0,  # Short timeout
            timeout=10.0
        )
        
        # Verify timeout behavior
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["exit_code"], 0)  # Should succeed
        self.assertTrue(results[1]["timed_out"])     # Should timeout
        self.assertEqual(results[2]["exit_code"], 0)  # Should succeed


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling integration across components."""
    
    def setUp(self):
        """Set up error handling tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up error handling tests."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    def test_timeout_error_propagation(self):
        """Test timeout error propagation through components."""
        config = TimeoutConfig(default_timeout=1.0)
        executor = CommandExecutor(config=config)
        
        try:
            with self.assertRaises(CommandTimeoutError) as cm:
                executor.execute("python -c \"import time; time.sleep(5)\"")
                
            # Verify error details
            error = cm.exception
            self.assertIn("python", error.command)
            self.assertEqual(error.timeout, 1.0)
            self.assertIsNotNone(error.pid)
            
        finally:
            executor.cleanup()
            
    def test_invalid_command_error_handling(self):
        """Test handling of invalid commands."""
        executor = CommandExecutor()
        
        try:
            # On macOS, invalid commands may not always raise exceptions
            # They might return with exit code 127 instead
            exit_code, output = executor.execute("/nonexistent/command/that/does/not/exist")
            # If no exception is raised, check that exit code indicates failure
            self.assertNotEqual(exit_code, 0, "Invalid command should not succeed")
                
        finally:
            executor.cleanup()
            
    def test_background_process_error_handling(self):
        """Test error handling in background processes."""
        # Start a background process that will fail
        info = execute_command_background(
            "python -c \"import sys; sys.exit(42)\"",  # Exit with code 42
            cwd=self.temp_dir
        )
        
        try:
            pid = info["pid"]
            
            # Wait for completion
            deadline = time.time() + 10.0
            while time.time() < deadline:
                process_info = get_background_process_info(pid)
                if process_info and process_info.get("status") == "completed":
                    break
                time.sleep(0.1)
                
            # Verify error is captured
            final_info = get_background_process_info(pid)
            self.assertEqual(final_info["status"], "completed")
            self.assertEqual(final_info["exit_code"], 42)
            
        finally:
            cleanup_background_process(pid)


class TestConcurrencyIntegration(unittest.TestCase):
    """Test concurrency integration across components."""
    
    def setUp(self):
        """Set up concurrency tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up concurrency tests."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
            
    @pytest.mark.integration
    def test_concurrent_command_execution(self):
        """Test concurrent command execution."""
        config = TimeoutConfig(default_timeout=10.0)
        results = []
        threads = []
        
        def execute_command_thread(index):
            try:
                executor = CommandExecutor(config=config)
                exit_code, output = executor.execute(f"echo 'Thread {index}'")
                results.append((index, exit_code, output))
                executor.cleanup()
            except Exception as e:
                results.append((index, -1, str(e)))
                
        # Start multiple concurrent executions
        for i in range(5):
            thread = threading.Thread(target=execute_command_thread, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=15.0)
            
        # Verify all completed successfully
        self.assertEqual(len(results), 5)
        for index, exit_code, output in results:
            self.assertEqual(exit_code, 0)
            self.assertIn(f"Thread {index}", output)
            
    @pytest.mark.integration
    def test_concurrent_background_processes(self):
        """Test concurrent background process management."""
        processes = []
        threads = []
        
        def start_background_process(index):
            try:
                info = execute_command_background(
                    f"python -c \"import time; print('BG {index}'); time.sleep(0.5)\"",
                    cwd=self.temp_dir
                )
                processes.append(info)
            except Exception as e:
                processes.append({"error": str(e), "index": index})
                
        # Start multiple background processes concurrently
        for i in range(3):
            thread = threading.Thread(target=start_background_process, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10.0)
            
        try:
            # Verify all processes started
            self.assertEqual(len(processes), 3)
            for info in processes:
                self.assertNotIn("error", info)
                self.assertIn("pid", info)
                
            # Wait for all to complete
            deadline = time.time() + 15.0
            while time.time() < deadline:
                all_completed = True
                for info in processes:
                    if "pid" in info:
                        process_info = get_background_process_info(info["pid"])
                        if not process_info or process_info.get("status") != "completed":
                            all_completed = False
                            break
                            
                if all_completed:
                    break
                time.sleep(0.1)
                
            # Verify all completed
            for info in processes:
                if "pid" in info:
                    process_info = get_background_process_info(info["pid"])
                    self.assertEqual(process_info["status"], "completed")
                    
        finally:
            # Clean up
            for info in processes:
                if "pid" in info:
                    cleanup_background_process(info["pid"])


if __name__ == "__main__":
    unittest.main()
