"""
Tests for timeout configuration functionality.

This module tests the TimeoutConfig class and related functionality.
"""

import pytest
import os
from unittest.mock import patch

from autocoder.common.shell_commands.timeout_config import TimeoutConfig
from autocoder.common.shell_commands.exceptions import TimeoutConfigError


class TestTimeoutConfig:
    """Test cases for TimeoutConfig class."""
    
    def test_default_creation(self):
        """Test creating TimeoutConfig with default values."""
        config = TimeoutConfig()
        assert config.default_timeout == 300.0
        assert config.interactive_timeout == 600.0
        assert config.cleanup_timeout == 10.0
        assert config.grace_period == 5.0
        assert len(config.command_timeouts) == 0
    
    def test_custom_values(self):
        """Test creating TimeoutConfig with custom values."""
        config = TimeoutConfig(
            default_timeout=120.0,
            interactive_timeout=300.0,
            cleanup_timeout=20.0,
            grace_period=10.0
        )
        assert config.default_timeout == 120.0
        assert config.interactive_timeout == 300.0
        assert config.cleanup_timeout == 20.0
        assert config.grace_period == 10.0
    
    def test_none_values_allowed(self):
        """Test that None values are allowed for optional timeouts."""
        config = TimeoutConfig(
            default_timeout=None,
            interactive_timeout=None
        )
        assert config.default_timeout is None
        assert config.interactive_timeout is None
    
    def test_validation_positive_values(self):
        """Test validation of positive timeout values."""
        with pytest.raises(TimeoutConfigError) as exc_info:
            TimeoutConfig(default_timeout=-1.0)
        assert "default_timeout" in str(exc_info.value)
        assert "positive" in str(exc_info.value).lower()
    
    def test_validation_zero_values(self):
        """Test validation with zero values."""
        with pytest.raises(TimeoutConfigError) as exc_info:
            TimeoutConfig(cleanup_timeout=0.0)
        assert "cleanup_timeout" in str(exc_info.value)
    
    def test_validation_grace_period(self):
        """Test validation of grace period."""
        with pytest.raises(TimeoutConfigError) as exc_info:
            TimeoutConfig(grace_period=-1.0)
        assert "grace_period" in str(exc_info.value)
    
    def test_command_timeout_setting(self):
        """Test setting command-specific timeout overrides."""
        config = TimeoutConfig()
        
        # Set single command timeout
        config.set_command_timeout("git", 60.0)
        assert config.get_timeout_for_command("git status") == 60.0
        
        # Set pattern timeout
        config.set_command_timeout("npm*", 180.0)
        assert config.get_timeout_for_command("npm install") == 180.0
        assert config.get_timeout_for_command("npm run build") == 180.0
    
    def test_command_timeout_validation(self):
        """Test validation of command timeout values."""
        config = TimeoutConfig()
        
        with pytest.raises(TimeoutConfigError) as exc_info:
            config.set_command_timeout("test", -1.0)
        assert "command_timeouts" in str(exc_info.value)
        assert "positive" in str(exc_info.value).lower()
    
    def test_get_timeout_for_command(self):
        """Test getting timeout for specific commands."""
        config = TimeoutConfig(default_timeout=60.0)
        
        # Default timeout
        assert config.get_timeout_for_command("echo hello") == 60.0
        
        # With override
        config.set_command_timeout("docker", 120.0)
        assert config.get_timeout_for_command("docker build") == 120.0
        assert config.get_timeout_for_command("docker run") == 120.0
    
    def test_wildcard_matching(self):
        """Test wildcard pattern matching."""
        config = TimeoutConfig(default_timeout=30.0)
        
        config.set_command_timeout("python*", 60.0)
        assert config.get_timeout_for_command("python script.py") == 60.0
        assert config.get_timeout_for_command("python3 script.py") == 60.0
        assert config.get_timeout_for_command("java Main") == 30.0
    
    def test_pattern_matching(self):
        """Test pattern matching behavior."""
        config = TimeoutConfig(default_timeout=30.0)
        
        # Exact match
        config.set_command_timeout("git", 60.0)
        assert config.get_timeout_for_command("git status") == 60.0
        
        # Substring match
        config.set_command_timeout("install", 120.0)
        assert config.get_timeout_for_command("npm install") == 120.0
        assert config.get_timeout_for_command("pip install") == 120.0
    
    def test_remove_command_timeout(self):
        """Test removing command timeout overrides."""
        config = TimeoutConfig()
        
        # Set and verify timeout
        config.set_command_timeout("test", 90.0)
        assert config.get_timeout_for_command("test") == 90.0
        
        # Remove timeout
        config.remove_command_timeout("test")
        assert config.get_timeout_for_command("test") == config.default_timeout
    
    def test_empty_command(self):
        """Test timeout for empty command."""
        config = TimeoutConfig(default_timeout=100.0)
        assert config.get_timeout_for_command("") == 100.0
        assert config.get_timeout_for_command("   ") == 100.0
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = TimeoutConfig(
            default_timeout=90.0,
            interactive_timeout=180.0,
            cleanup_timeout=15.0,
            grace_period=7.0
        )
        config.set_command_timeout("test", 45.0)
        
        config_dict = config.to_dict()
        assert config_dict["default_timeout"] == 90.0
        assert config_dict["interactive_timeout"] == 180.0
        assert config_dict["cleanup_timeout"] == 15.0
        assert config_dict["grace_period"] == 7.0
        assert config_dict["command_timeouts"]["test"] == 45.0
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "default_timeout": 90.0,
            "interactive_timeout": 180.0,
            "cleanup_timeout": 15.0,
            "grace_period": 7.0,
            "command_timeouts": {"test": 45.0, "git": 60.0}
        }
        
        config = TimeoutConfig.from_dict(config_dict)
        assert config.default_timeout == 90.0
        assert config.interactive_timeout == 180.0
        assert config.cleanup_timeout == 15.0
        assert config.grace_period == 7.0
        assert config.get_timeout_for_command("test") == 45.0
        assert config.get_timeout_for_command("git") == 60.0
    
    def test_from_dict_with_missing_fields(self):
        """Test creating config from dictionary with missing fields."""
        config_dict = {"default_timeout": 120.0}
        
        config = TimeoutConfig.from_dict(config_dict)
        assert config.default_timeout == 120.0
        # Other fields should have defaults
        assert config.interactive_timeout == 600.0
        assert config.cleanup_timeout == 10.0
        assert config.grace_period == 5.0
    
    def test_from_dict_with_invalid_data(self):
        """Test creating config from dictionary with invalid data."""
        config_dict = {"default_timeout": -1.0}
        
        with pytest.raises(TimeoutConfigError):
            TimeoutConfig.from_dict(config_dict)
    
    def test_command_timeouts_initialization(self):
        """Test initialization with command timeouts."""
        command_timeouts = {"git": 60.0, "npm*": 120.0}
        config = TimeoutConfig(command_timeouts=command_timeouts)
        
        assert config.get_timeout_for_command("git") == 60.0
        assert config.get_timeout_for_command("npm install") == 120.0
    
    def test_command_timeouts_validation_on_init(self):
        """Test validation of command timeouts during initialization."""
        with pytest.raises(TimeoutConfigError) as exc_info:
            TimeoutConfig(command_timeouts={"test": -1.0})
        assert "command_timeouts" in str(exc_info.value)


class TestTimeoutConfigEnvironment:
    """Test cases for environment-based configuration."""
    
    def test_from_env_no_env_vars(self):
        """Test creating config from environment with no env vars set."""
        config = TimeoutConfig.from_env()
        # Should use defaults
        assert config.default_timeout == 300.0
        assert config.interactive_timeout == 600.0
    
    @patch.dict(os.environ, {
        'AUTOCODER_DEFAULT_TIMEOUT': '120',
        'AUTOCODER_INTERACTIVE_TIMEOUT': '240',
        'AUTOCODER_CLEANUP_TIMEOUT': '20',
        'AUTOCODER_GRACE_PERIOD': '8'
    })
    def test_from_env_with_env_vars(self):
        """Test creating config from environment variables."""
        config = TimeoutConfig.from_env()
        assert config.default_timeout == 120.0
        assert config.interactive_timeout == 240.0
        assert config.cleanup_timeout == 20.0
        assert config.grace_period == 8.0
    
    @patch.dict(os.environ, {
        'AUTOCODER_DEFAULT_TIMEOUT': 'none'
    })
    def test_from_env_with_none_values(self):
        """Test creating config from environment with 'none' values."""
        config = TimeoutConfig.from_env()
        assert config.default_timeout is None
        assert config.interactive_timeout == 600.0  # default
    
    @patch.dict(os.environ, {
        'AUTOCODER_DEFAULT_TIMEOUT': 'invalid'
    })
    def test_from_env_with_invalid_env_var(self):
        """Test creating config from environment with invalid values."""
        with pytest.raises(TimeoutConfigError) as exc_info:
            TimeoutConfig.from_env()
        assert "AUTOCODER_DEFAULT_TIMEOUT" in str(exc_info.value)


class TestTimeoutConfigStringRepresentation:
    """Test cases for string representation."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        config = TimeoutConfig(default_timeout=100.0)
        config.set_command_timeout("test", 50.0)
        
        str_repr = str(config)
        assert "TimeoutConfig" in str_repr
        assert "100.0" in str_repr
        assert "overrides=1" in str_repr
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        config = TimeoutConfig(
            default_timeout=100.0,
            interactive_timeout=200.0
        )
        config.set_command_timeout("test", 50.0)
        
        repr_str = repr(config)
        assert "TimeoutConfig" in repr_str
        assert "default_timeout=100.0" in repr_str
        assert "interactive_timeout=200.0" in repr_str
        assert "test" in repr_str


class TestTimeoutConfigEdgeCases:
    """Test cases for edge cases and error conditions."""
    
    def test_matches_pattern_edge_cases(self):
        """Test pattern matching edge cases."""
        config = TimeoutConfig()
        
        # Test with various patterns
        config.set_command_timeout("*test", 60.0)
        assert config.get_timeout_for_command("mytest") == 60.0
        
        config.set_command_timeout("test*", 90.0)
        assert config.get_timeout_for_command("test123") == 90.0
    
    def test_command_priority(self):
        """Test command matching priority."""
        config = TimeoutConfig(default_timeout=30.0)
        
        # Set multiple overlapping patterns
        config.set_command_timeout("npm", 60.0)  # exact match
        config.set_command_timeout("npm*", 90.0)  # wildcard match
        
        # Exact match should take precedence
        assert config.get_timeout_for_command("npm") == 60.0
        assert config.get_timeout_for_command("npm install") == 90.0
    
    def test_dataclass_behavior(self):
        """Test that TimeoutConfig behaves as a proper dataclass."""
        config1 = TimeoutConfig(default_timeout=100.0)
        config2 = TimeoutConfig(default_timeout=100.0)
        
        # Should be equal with same values
        assert config1 == config2
        
        # Should be different with different values
        config2.default_timeout = 200.0
        assert config1 != config2
    
    def test_field_assignment(self):
        """Test direct field assignment."""
        config = TimeoutConfig()
        
        # Direct assignment should work
        config.default_timeout = 150.0
        assert config.default_timeout == 150.0
        
        # But validation won't be called automatically
        # (this is a limitation of dataclasses)
    
    def test_command_timeouts_modification(self):
        """Test direct modification of command_timeouts dict."""
        config = TimeoutConfig()
        
        # Direct modification should work
        config.command_timeouts["direct"] = 75.0
        assert config.get_timeout_for_command("direct") == 75.0
        
        # But it bypasses validation
        # (again, dataclass limitation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 