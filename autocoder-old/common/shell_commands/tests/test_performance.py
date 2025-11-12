"""
Performance tests for Shell Commands module.

This module provides performance tests to verify that the shell commands
system performs well under various load conditions including high
throughput, concurrent operations, memory usage, and stress scenarios.
"""

import unittest
import pytest
import time
import threading
import tempfile
import os
import psutil
import statistics
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from autocoder.common.shell_commands import (
    CommandExecutor,
    TimeoutConfig,
    execute_command,
    execute_command_background,
    execute_commands,
    get_background_processes,
    cleanup_background_process,
    InteractiveCommandExecutor,
    get_session_manager,
    get_background_process_notifier
)


class PerformanceTestCase(unittest.TestCase):
    """Base class for performance tests with common utilities."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.start_memory = self._get_memory_usage()
        self.performance_data = {}
        
    def tearDown(self):
        """Clean up performance test environment."""
        # Clean up any remaining processes
        try:
            bg_processes = get_background_processes()
            for pid in bg_processes.keys():
                cleanup_background_process(pid)
        except:
            pass
            
        # Clean up sessions
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
            
        # Report memory usage
        end_memory = self._get_memory_usage()
        memory_diff = end_memory - self.start_memory
        if memory_diff > 50 * 1024 * 1024:  # 50MB threshold
            print(f"Warning: Memory usage increased by {memory_diff / 1024 / 1024:.1f}MB")
            
    def _get_memory_usage(self) -> int:
        """Get current process memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except:
            return 0
            
    def _measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
        
    def _measure_throughput(self, func, iterations: int, *args, **kwargs) -> Tuple[List[Any], float]:
        """Measure throughput of a function over multiple iterations."""
        results = []
        start_time = time.time()
        
        for _ in range(iterations):
            result = func(*args, **kwargs)
            results.append(result)
            
        end_time = time.time()
        total_time = end_time - start_time
        throughput = iterations / total_time if total_time > 0 else 0
        
        return results, throughput


@pytest.mark.performance
class TestCommandExecutionPerformance(PerformanceTestCase):
    """Test command execution performance."""
    
    def test_single_command_performance(self):
        """Test performance of single command execution."""
        config = TimeoutConfig(default_timeout=30.0)
        executor = CommandExecutor(config=config)
        
        try:
            # Measure simple command execution
            _, duration = self._measure_time(
                executor.execute, "echo 'performance test'"
            )
            
            # Should complete quickly
            self.assertLess(duration, 1.0, "Simple command should complete in under 1 second")
            
            # Measure multiple executions for consistency
            durations = []
            for _ in range(10):
                _, duration = self._measure_time(
                    executor.execute, "echo 'test'"
                )
                durations.append(duration)
                
            avg_duration = statistics.mean(durations)
            std_deviation = statistics.stdev(durations) if len(durations) > 1 else 0
            
            self.assertLess(avg_duration, 0.5, "Average execution time should be reasonable")
            self.assertLess(std_deviation, 0.2, "Execution time should be consistent")
            
        finally:
            executor.cleanup()
            
    def test_concurrent_command_execution_performance(self):
        """Test performance under concurrent command execution."""
        num_threads = 10
        commands_per_thread = 5
        
        def execute_commands_worker():
            config = TimeoutConfig(default_timeout=10.0)
            executor = CommandExecutor(config=config)
            durations = []
            
            try:
                for i in range(commands_per_thread):
                    _, duration = self._measure_time(
                        executor.execute, f"echo 'worker command {i}'"
                    )
                    durations.append(duration)
                return durations
            finally:
                executor.cleanup()
                
        # Execute commands concurrently
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(execute_commands_worker) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
            
        total_time = time.time() - start_time
        
        # Calculate statistics
        all_durations = [duration for worker_durations in results for duration in worker_durations]
        total_commands = num_threads * commands_per_thread
        avg_duration = statistics.mean(all_durations)
        throughput = total_commands / total_time
        
        # Performance assertions
        self.assertGreater(throughput, 10, "Should achieve reasonable throughput")
        self.assertLess(avg_duration, 2.0, "Average command duration should be reasonable")
        self.assertLess(total_time, 30.0, "Total execution time should be reasonable")
        
        print(f"Concurrent execution: {total_commands} commands in {total_time:.2f}s "
              f"(throughput: {throughput:.1f} cmd/s, avg: {avg_duration:.3f}s)")
              
    def test_batch_execution_performance(self):
        """Test batch execution performance."""
        # Test parallel batch execution
        commands = [f"echo 'batch command {i}'" for i in range(20)]
        
        # Measure parallel execution
        parallel_results, parallel_time = self._measure_time(
            execute_commands, commands, parallel=True, timeout=30.0
        )
        
        # Measure serial execution
        serial_results, serial_time = self._measure_time(
            execute_commands, commands, parallel=False, timeout=60.0
        )
        
        # Verify all commands succeeded
        self.assertEqual(len(parallel_results), 20)
        self.assertEqual(len(serial_results), 20)
        
        for result in parallel_results + serial_results:
            self.assertEqual(result["exit_code"], 0)
            
        # Parallel should be significantly faster for I/O bound tasks
        speedup_ratio = serial_time / parallel_time if parallel_time > 0 else 1
        
        print(f"Batch execution: Parallel {parallel_time:.2f}s vs Serial {serial_time:.2f}s "
              f"(speedup: {speedup_ratio:.1f}x)")
              
        # Allow for some overhead, but parallel should still be faster
        self.assertLess(parallel_time, serial_time * 0.8, 
                       "Parallel execution should be significantly faster")


@pytest.mark.performance  
class TestBackgroundProcessPerformance(PerformanceTestCase):
    """Test background process performance."""
    
    def test_background_process_creation_performance(self):
        """Test performance of background process creation."""
        num_processes = 20
        processes = []
        
        try:
            # Measure batch creation
            creation_durations = []
            for i in range(num_processes):
                _, duration = self._measure_time(
                    execute_command_background,
                    f"python -c \"import time; print('bg {i}'); time.sleep(0.1)\"",
                    cwd=self.temp_dir
                )
                creation_durations.append(duration)
                # Track for cleanup
                processes.append(_)
                
            avg_creation_time = statistics.mean(creation_durations)
            max_creation_time = max(creation_durations)
            
            # Performance assertions
            self.assertLess(avg_creation_time, 0.5, "Background process creation should be fast")
            self.assertLess(max_creation_time, 2.0, "No single creation should be too slow")
            
            print(f"Background process creation: avg {avg_creation_time:.3f}s, "
                  f"max {max_creation_time:.3f}s for {num_processes} processes")
                  
            # Verify all processes are tracked
            bg_processes = get_background_processes()
            active_count = len([p for p in bg_processes.values() if p.get("status") == "running"])
            self.assertGreaterEqual(active_count, num_processes * 0.5)  # At least half should still be running
            
        finally:
            # Clean up all processes
            for info in processes:
                if isinstance(info, dict) and "pid" in info:
                    cleanup_background_process(info["pid"])
                    
    def test_background_process_monitoring_performance(self):
        """Test performance of background process monitoring."""
        num_processes = 10
        processes = []
        
        try:
            # Start background processes
            for i in range(num_processes):
                info = execute_command_background(
                    f"python -c \"import time; time.sleep(2); print('done {i}')\"",
                    cwd=self.temp_dir
                )
                processes.append(info)
                
            # Measure monitoring performance
            monitoring_durations = []
            for _ in range(20):  # Multiple monitoring cycles
                _, duration = self._measure_time(get_background_processes)
                monitoring_durations.append(duration)
                time.sleep(0.1)
                
            avg_monitoring_time = statistics.mean(monitoring_durations)
            max_monitoring_time = max(monitoring_durations)
            
            # Performance assertions
            self.assertLess(avg_monitoring_time, 0.1, "Process monitoring should be fast")
            self.assertLess(max_monitoring_time, 0.5, "No monitoring call should be too slow")
            
            print(f"Background process monitoring: avg {avg_monitoring_time:.3f}s, "
                  f"max {max_monitoring_time:.3f}s per call")
                  
        finally:
            # Clean up
            for info in processes:
                cleanup_background_process(info["pid"])
                
    def test_background_process_notifier_performance(self):
        """Test background process notifier performance."""
        import uuid
        
        conv_id = f"perf-test-{uuid.uuid4()}"
        notifier = get_background_process_notifier()
        num_processes = 15
        processes = []
        
        try:
            # Start multiple background processes and register them
            registration_durations = []
            for i in range(num_processes):
                info = execute_command_background(
                    f"python -c \"import time; time.sleep(0.5); print('notifier test {i}')\"",
                    cwd=self.temp_dir
                )
                processes.append(info)
                
                # Measure registration time
                _, duration = self._measure_time(
                    notifier.register_process,
                    conversation_id=conv_id,
                    pid=info["pid"],
                    tool_name="perf_test",
                    command=info["command"],
                    cwd=self.temp_dir
                )
                registration_durations.append(duration)
                
            avg_registration_time = statistics.mean(registration_durations)
            
            # Test message polling performance
            polling_durations = []
            total_messages = 0
            
            # Poll for completion messages
            deadline = time.time() + 30.0
            while time.time() < deadline:
                _, duration = self._measure_time(
                    notifier.poll_messages, conv_id, 10
                )
                polling_durations.append(duration)
                
                messages = notifier.poll_messages(conv_id, 10)
                total_messages += len(messages)
                
                if total_messages >= num_processes:
                    break
                    
                time.sleep(0.1)
                
            if polling_durations:
                avg_polling_time = statistics.mean(polling_durations)
                max_polling_time = max(polling_durations)
                
                # Performance assertions
                self.assertLess(avg_registration_time, 0.1, "Process registration should be fast")
                self.assertLess(avg_polling_time, 0.05, "Message polling should be very fast")
                self.assertLess(max_polling_time, 0.2, "No polling should be too slow")
                
                print(f"Notifier performance: registration avg {avg_registration_time:.3f}s, "
                      f"polling avg {avg_polling_time:.3f}s")
                      
        finally:
            # Clean up
            for info in processes:
                cleanup_background_process(info["pid"])


@pytest.mark.performance
class TestInteractiveSessionPerformance(PerformanceTestCase):
    """Test interactive session performance."""
    
    def test_session_creation_performance(self):
        """Test performance of interactive session creation."""
        manager = get_session_manager()
        num_sessions = 10
        session_ids = []
        
        try:
            # Measure session creation
            creation_durations = []
            for i in range(num_sessions):
                _, duration = self._measure_time(
                    manager.create_session,
                    f"python -c \"print('session {i}'); import time; time.sleep(0.5)\"",
                    timeout=30,
                    use_pexpect=False
                )
                creation_durations.append(duration)
                
                if _.success:
                    session_ids.append(_.content["session_id"])
                    
            avg_creation_time = statistics.mean(creation_durations)
            successful_sessions = len(session_ids)
            
            # Performance assertions
            self.assertLess(avg_creation_time, 2.0, "Session creation should be reasonably fast")
            self.assertGreaterEqual(successful_sessions, num_sessions * 0.8, "Most sessions should be created successfully")
            
            print(f"Session creation: avg {avg_creation_time:.3f}s for {successful_sessions}/{num_sessions} sessions")
            
        finally:
            # Clean up sessions
            for session_id in session_ids:
                try:
                    manager.terminate_session(session_id)
                except:
                    pass
                    
    def test_session_communication_performance(self):
        """Test performance of session communication."""
        manager = get_session_manager()
        
        # Create a session
        result = manager.create_session(
            "python -c \"import sys; [print(input()) for _ in range(100)]\"",
            timeout=60,
            use_pexpect=False
        )
        
        if not result.success:
            self.skipTest("Could not create session for performance test")
            
        session_id = result.content["session_id"]
        
        try:
            # Measure input/output performance
            communication_durations = []
            for i in range(20):
                # Measure sending input
                _, send_duration = self._measure_time(
                    manager.send_input, session_id, f"Message {i}\n"
                )
                
                # Small delay to let command process
                time.sleep(0.05)
                
                # Measure reading output  
                _, read_duration = self._measure_time(
                    manager.read_output, session_id
                )
                
                total_duration = send_duration + read_duration
                communication_durations.append(total_duration)
                
            avg_communication_time = statistics.mean(communication_durations)
            max_communication_time = max(communication_durations)
            
            # Performance assertions
            self.assertLess(avg_communication_time, 0.5, "Session communication should be fast")
            self.assertLess(max_communication_time, 2.0, "No single communication should be too slow")
            
            print(f"Session communication: avg {avg_communication_time:.3f}s, "
                  f"max {max_communication_time:.3f}s per round-trip")
                  
        finally:
            manager.terminate_session(session_id)
            
    def test_concurrent_session_performance(self):
        """Test performance with multiple concurrent sessions."""
        manager = get_session_manager()
        num_sessions = 8  # Reasonable number for concurrent testing
        
        def session_worker(session_index):
            """Worker function for concurrent session testing."""
            timings = []
            session_id = None
            
            try:
                # Create session
                start_time = time.time()
                result = manager.create_session(
                    f"python -c \"import time; print('session {session_index} ready'); "
                    f"[print(input()) for _ in range(5)]\"",
                    timeout=30,
                    use_pexpect=False
                )
                creation_time = time.time() - start_time
                
                if not result.success:
                    return {"error": f"Failed to create session {session_index}"}
                    
                session_id = result.content["session_id"]
                timings.append(("creation", creation_time))
                
                # Perform some communication
                for i in range(5):
                    start_time = time.time()
                    manager.send_input(session_id, f"Message {i} from session {session_index}\n")
                    time.sleep(0.02)  # Small delay
                    manager.read_output(session_id)
                    comm_time = time.time() - start_time
                    timings.append(("communication", comm_time))
                    
                return {"session_index": session_index, "timings": timings}
                
            except Exception as e:
                return {"error": f"Session {session_index} error: {str(e)}"}
            finally:
                if session_id:
                    try:
                        manager.terminate_session(session_id)
                    except:
                        pass
                        
        # Execute concurrent sessions
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_sessions) as executor:
            futures = [executor.submit(session_worker, i) for i in range(num_sessions)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Analyze results
        successful_sessions = [r for r in results if "error" not in r]
        failed_sessions = [r for r in results if "error" in r]
        
        if failed_sessions:
            print(f"Failed sessions: {len(failed_sessions)}")
            for failure in failed_sessions:
                print(f"  {failure['error']}")
                
        self.assertGreater(len(successful_sessions), num_sessions * 0.7, 
                          "Most concurrent sessions should succeed")
                          
        if successful_sessions:
            all_timings = []
            for session_result in successful_sessions:
                all_timings.extend(session_result["timings"])
                
            creation_times = [t[1] for t in all_timings if t[0] == "creation"]
            communication_times = [t[1] for t in all_timings if t[0] == "communication"]
            
            if creation_times:
                avg_creation = statistics.mean(creation_times)
                print(f"Concurrent sessions: {len(successful_sessions)} sessions, "
                      f"avg creation {avg_creation:.3f}s, total time {total_time:.2f}s")
                      
                self.assertLess(avg_creation, 5.0, "Concurrent session creation should be reasonable")


@pytest.mark.performance
class TestMemoryPerformance(PerformanceTestCase):
    """Test memory usage performance."""
    
    def test_memory_usage_under_load(self):
        """Test memory usage under high load."""
        initial_memory = self._get_memory_usage()
        
        # Create multiple executors and run commands
        executors = []
        try:
            for i in range(10):
                config = TimeoutConfig(default_timeout=30.0)
                executor = CommandExecutor(config=config)
                executors.append(executor)
                
                # Execute some commands
                for j in range(5):
                    executor.execute(f"echo 'executor {i} command {j}'")
                    
            # Check memory usage after load
            peak_memory = self._get_memory_usage()
            memory_increase = peak_memory - initial_memory
            
            print(f"Memory usage: initial {initial_memory // 1024 // 1024}MB, "
                  f"peak {peak_memory // 1024 // 1024}MB, "
                  f"increase {memory_increase // 1024 // 1024}MB")
                  
            # Memory increase should be reasonable (less than 100MB for this test)
            self.assertLess(memory_increase, 100 * 1024 * 1024, 
                           "Memory usage should not increase excessively")
                           
        finally:
            # Clean up executors
            for executor in executors:
                executor.cleanup()
                
            # Force garbage collection
            import gc
            gc.collect()
            
            # Check memory after cleanup
            final_memory = self._get_memory_usage()
            memory_after_cleanup = final_memory - initial_memory
            
            print(f"Memory after cleanup: {final_memory // 1024 // 1024}MB, "
                  f"net increase {memory_after_cleanup // 1024 // 1024}MB")
                  
    def test_background_process_memory_scaling(self):
        """Test memory usage with many background processes."""
        initial_memory = self._get_memory_usage()
        processes = []
        
        try:
            # Start many short-lived background processes
            for i in range(50):
                info = execute_command_background(
                    f"python -c \"import time; time.sleep(0.2); print('done {i}')\"",
                    cwd=self.temp_dir
                )
                processes.append(info)
                
                # Check memory periodically
                if i % 10 == 0:
                    current_memory = self._get_memory_usage()
                    memory_per_process = (current_memory - initial_memory) // (i + 1) if i > 0 else 0
                    print(f"After {i+1} processes: {memory_per_process // 1024}KB per process")
                    
            # Wait for processes to complete
            deadline = time.time() + 30.0
            while time.time() < deadline:
                bg_processes = get_background_processes()
                active_count = len([p for p in bg_processes.values() if p.get("status") == "running"])
                if active_count == 0:
                    break
                time.sleep(0.5)
                
            peak_memory = self._get_memory_usage()
            total_increase = peak_memory - initial_memory
            memory_per_process = total_increase // len(processes)
            
            print(f"Memory scaling: {len(processes)} processes, "
                  f"total increase {total_increase // 1024 // 1024}MB, "
                  f"~{memory_per_process // 1024}KB per process")
                  
            # Each process shouldn't use excessive memory
            self.assertLess(memory_per_process, 5 * 1024 * 1024,  # 5MB per process
                           "Memory per process should be reasonable")
                           
        finally:
            # Clean up
            for info in processes:
                cleanup_background_process(info["pid"])


if __name__ == "__main__":
    # Run performance tests with verbose output
    unittest.main(verbosity=2)
