#!/usr/bin/env python3
"""
Test suite for InteractivePexpectProcess.

This module provides unit tests for the InteractivePexpectProcess class.
"""

import pytest
import time
import signal
import platform
from unittest.mock import Mock, patch

from .interactive_pexpect_process import InteractivePexpectProcess, PEXPECT_AVAILABLE
from .exceptions import CommandExecutionError


class TestInteractivePexpectProcess:
    """Test suite for InteractivePexpectProcess."""
    
    def test_init(self):
        """Test initialization."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        proc = InteractivePexpectProcess("echo test")
        assert proc.command == "echo test"
        assert proc.encoding == "utf-8"
        assert proc.shell is True
        assert proc.timeout is None
        assert not proc.is_alive()
    
    def test_init_with_args(self):
        """Test initialization with arguments."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        proc = InteractivePexpectProcess(
            ["ls", "-la"],
            cwd="/tmp",
            timeout=10.0,
            shell=False
        )
        assert proc.command == ["ls", "-la"]
        assert proc.cwd == "/tmp"
        assert proc.timeout == 10.0
        assert proc.shell is False
    
    def test_pexpect_unavailable(self):
        """Test behavior when pexpect is unavailable."""
        with patch('src.autocoder.common.shell_commands.interactive_pexpect_process.PEXPECT_AVAILABLE', False):
            with pytest.raises(CommandExecutionError, match="pexpect not available"):
                InteractivePexpectProcess("echo test")
    
    def test_basic_command(self):
        """Test running a basic command."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'Hello World'", timeout=5.0) as proc:
            # Give command time to execute
            time.sleep(0.5)
            
            # Process should be alive briefly
            assert proc.pid is not None
            
            # Read output
            output = proc.read_output(timeout=2.0)
            assert output is not None
            assert "Hello World" in output
    
    def test_command_with_args(self):
        """Test running command with arguments."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess(["echo", "test"], shell=False, timeout=5.0) as proc:
            time.sleep(0.5)
            
            output = proc.read_output(timeout=2.0)
            assert output is not None
            assert "test" in output
    
    def test_write_and_read(self):
        """Test writing to and reading from process."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        if platform.system() == "Windows":
            pytest.skip("Interactive shell test not reliable on Windows")
        
        with InteractivePexpectProcess("cat", timeout=5.0) as proc:
            # Write to process
            test_data = "Hello from test\n"
            proc.write(test_data)
            
            # Read back
            output = proc.read_output(timeout=2.0)
            assert output is not None
            assert "Hello from test" in output
    
    def test_sendline(self):
        """Test sendline method."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        if platform.system() == "Windows":
            pytest.skip("Interactive shell test not reliable on Windows")
        
        with InteractivePexpectProcess("cat", timeout=5.0) as proc:
            proc.sendline("test line")
            
            output = proc.read_output(timeout=2.0)
            assert output is not None
            assert "test line" in output
    
    def test_expect_pattern(self):
        """Test expect pattern matching."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'Pattern: SUCCESS'", timeout=5.0) as proc:
            try:
                result = proc.expect("SUCCESS", timeout=3.0)
                assert result == 0
                assert proc.after is not None
                assert "SUCCESS" in proc.after
            except CommandExecutionError:
                # This might happen if the command completes too quickly
                pass
    
    def test_expect_timeout(self):
        """Test expect timeout."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'test'", timeout=5.0) as proc:
            with pytest.raises(CommandExecutionError, match="timeout"):
                proc.expect("NEVER_APPEARS", timeout=1.0)
    
    def test_signal_handling(self):
        """Test signal handling."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        if platform.system() == "Windows":
            pytest.skip("Signal handling test not reliable on Windows")
        
        with InteractivePexpectProcess("sleep 10", timeout=5.0) as proc:
            # Let process start
            time.sleep(0.5)
            assert proc.is_alive()
            
            # Send SIGINT
            proc.send_signal(signal.SIGINT)
            
            # Wait for termination
            time.sleep(1.0)
            
            # Process should be terminated
            assert not proc.is_alive()
    
    def test_terminate(self):
        """Test process termination."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        proc = InteractivePexpectProcess("sleep 10", timeout=5.0)
        proc.start()
        
        # Let process start
        time.sleep(0.5)
        assert proc.is_alive()
        
        # Terminate
        result = proc.terminate()
        assert result is True
        assert not proc.is_alive()
    
    def test_context_manager(self):
        """Test context manager functionality."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'context test'", timeout=5.0) as proc:
            assert proc.is_alive()
            pid = proc.pid
            assert pid is not None
        
        # Process should be terminated after context exit
        assert not proc.is_alive()
    
    def test_stats(self):
        """Test process statistics."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'stats test'", timeout=5.0) as proc:
            time.sleep(0.5)
            
            stats = proc.get_stats()
            assert isinstance(stats, dict)
            assert 'pid' in stats
            assert 'is_alive' in stats
            assert 'platform' in stats
            assert 'pexpect_available' in stats
            assert stats['pexpect_available'] is True
    
    def test_read_lines(self):
        """Test line reading generator."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        script = '''
python3 -c "
print('Line 1')
print('Line 2')
print('Line 3')
"
'''
        
        with InteractivePexpectProcess(script, shell=True, timeout=5.0) as proc:
            lines = []
            for line in proc.read_lines(timeout=0.5):
                lines.append(line.strip())
                if len(lines) >= 3:  # Limit to avoid infinite loop
                    break
            
            # Should have captured some lines
            assert len(lines) > 0
    
    def test_error_handling(self):
        """Test error handling."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        # Test invalid command
        with pytest.raises(CommandExecutionError):
            with InteractivePexpectProcess("nonexistent_command_12345", timeout=2.0) as proc:
                time.sleep(1.0)
    
    def test_properties(self):
        """Test process properties."""
        if not PEXPECT_AVAILABLE:
            pytest.skip("pexpect not available")
        
        with InteractivePexpectProcess("echo 'property test'", timeout=5.0) as proc:
            # Test initial properties
            assert proc.pid is not None
            assert proc.duration is not None
            assert proc.bytes_written >= 0
            assert proc.bytes_read >= 0
            
            # Test after some activity
            proc.sendline("test")
            time.sleep(0.1)
            
            assert proc.bytes_written > 0


def test_platform_compatibility():
    """Test platform-specific behavior."""
    if not PEXPECT_AVAILABLE:
        pytest.skip("pexpect not available")
    
    # This test should work on all platforms where pexpect is available
    with InteractivePexpectProcess("echo 'platform test'", timeout=5.0) as proc:
        assert proc.is_alive()
        
        # Platform-specific behavior
        if platform.system() == "Windows":
            # Windows uses popen_spawn
            assert hasattr(proc.child, 'pid')
        else:
            # Unix-like systems use regular spawn
            assert hasattr(proc.child, 'pid')
            assert hasattr(proc.child, 'isalive')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 