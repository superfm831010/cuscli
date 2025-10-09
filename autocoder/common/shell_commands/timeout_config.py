"""
Timeout configuration module for shell command execution.

This module provides flexible timeout configuration for different types of commands
and execution scenarios.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, Union, List

from .exceptions import TimeoutConfigError


@dataclass
class TimeoutConfig:
    """
    Configuration class for command timeout settings.
    
    This class provides comprehensive timeout configuration including:
    - Default timeout for all commands
    - Interactive command timeout
    - Process cleanup timeout
    - Grace period for graceful termination
    - Command-specific timeout overrides
    
    Attributes:
        default_timeout: Default timeout for all commands (seconds)
        interactive_timeout: Timeout for interactive commands (seconds)
        cleanup_timeout: Timeout for process cleanup operations (seconds)
        grace_period: Grace period for graceful process termination (seconds)
        command_timeouts: Dictionary mapping command patterns to specific timeouts
    """
    
    default_timeout: Optional[float] = 300.0  # 5 minutes
    interactive_timeout: Optional[float] = 600.0  # 10 minutes
    cleanup_timeout: float = 10.0  # 10 seconds
    grace_period: float = 5.0  # 5 seconds
    
    # Command-specific timeout overrides
    command_timeouts: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate timeout configuration values."""
        
        # Validate default_timeout
        if self.default_timeout is not None and self.default_timeout <= 0:
            raise TimeoutConfigError(
                "default_timeout", 
                self.default_timeout, 
                "must be positive or None"
            )
        
        # Validate interactive_timeout
        if self.interactive_timeout is not None and self.interactive_timeout <= 0:
            raise TimeoutConfigError(
                "interactive_timeout", 
                self.interactive_timeout, 
                "must be positive or None"
            )
        
        # Validate cleanup_timeout
        if self.cleanup_timeout <= 0:
            raise TimeoutConfigError(
                "cleanup_timeout", 
                self.cleanup_timeout, 
                "must be positive"
            )
        
        # Validate grace_period
        if self.grace_period <= 0:
            raise TimeoutConfigError(
                "grace_period", 
                self.grace_period, 
                "must be positive"
            )
        
        # Validate command_timeouts
        for command, timeout in self.command_timeouts.items():
            if timeout <= 0:
                raise TimeoutConfigError(
                    f"command_timeouts[{command}]", 
                    timeout, 
                    "must be positive"
                )
    
    def get_timeout_for_command(self, command: Union[str, List[str]]) -> Optional[float]:
        """
        Get the appropriate timeout for a specific command.
        
        This method checks for command-specific timeouts first, then falls back
        to the default timeout.
        
        Args:
            command: The command string or list to get timeout for
            
        Returns:
            Timeout in seconds, or None for no timeout
        """
        # Convert command to string if needed
        if isinstance(command, list):
            if not command:
                return self.default_timeout
            command_str = " ".join(str(arg) for arg in command)
        else:
            command_str = command
            
        if not command_str:
            return self.default_timeout
        
        # Extract the base command (first word)
        base_command = command_str.strip().split()[0] if command_str.strip() else ""
        command_parts = command_str.strip().split()
        is_single_command = len(command_parts) == 1
        
        # Check for pattern matches - prioritize patterns that match from the beginning
        # Sort patterns by specificity: exact matches first for single commands, then patterns, then exact for multi-word
        def pattern_priority(item):
            pattern, _ = item
            # For single-word commands, exact matches get highest priority
            # For multi-word commands, patterns get higher priority than base command exact matches
            is_exact = pattern == base_command
            is_pattern = '*' in pattern
            # Patterns starting with text (not *) get higher priority than wildcards
            starts_with_text = not pattern.startswith('*')
            # Longer patterns get higher priority within same category
            length = len(pattern)
            
            if is_single_command:
                # Single command: exact > patterns
                return (is_exact, not is_pattern, starts_with_text, length)
            else:
                # Multi-word command: patterns > exact base command
                return (not is_exact or is_pattern, starts_with_text, length)
        
        patterns = sorted(self.command_timeouts.items(), key=pattern_priority, reverse=True)
        
        for pattern, timeout in patterns:
            # For exact matches, check base command
            if pattern == base_command and ('*' not in pattern):
                # For multi-word commands, only return exact match if no patterns match
                if is_single_command:
                    return timeout
                # For multi-word, continue to check patterns first
            # For patterns, check full command string
            if self._matches_pattern(command_str, pattern):
                return timeout
        
        # If we get here and it's a multi-word command, check for exact base command match
        if not is_single_command and base_command in self.command_timeouts:
            pattern = base_command
            if '*' not in pattern:  # Make sure it's not a pattern
                return self.command_timeouts[base_command]
        
        # Fall back to default timeout
        return self.default_timeout
    
    def _matches_pattern(self, command: str, pattern: str) -> bool:
        """
        Check if a command matches a timeout pattern.
        
        Args:
            command: The command to check
            pattern: The pattern to match against
            
        Returns:
            True if the command matches the pattern
        """
        # Support simple wildcard patterns
        if '*' in pattern:
            # Convert simple wildcard to regex
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, command))
        
        # Support exact substring matching
        return pattern in command
    
    def set_command_timeout(self, command_pattern: str, timeout: float):
        """
        Set timeout for a specific command pattern.
        
        Args:
            command_pattern: Command or pattern to set timeout for
            timeout: Timeout value in seconds
            
        Raises:
            TimeoutConfigError: If timeout value is invalid
        """
        if timeout <= 0:
            raise TimeoutConfigError(
                f"command_timeouts[{command_pattern}]", 
                timeout, 
                "must be positive"
            )
        
        self.command_timeouts[command_pattern] = timeout
    
    def remove_command_timeout(self, command_pattern: str):
        """
        Remove timeout override for a command pattern.
        
        Args:
            command_pattern: Command pattern to remove
        """
        self.command_timeouts.pop(command_pattern, None)
    
    @classmethod
    def from_env(cls) -> 'TimeoutConfig':
        """
        Create TimeoutConfig from environment variables.
        
        Environment variables:
            AUTOCODER_DEFAULT_TIMEOUT: Default timeout in seconds
            AUTOCODER_INTERACTIVE_TIMEOUT: Interactive timeout in seconds
            AUTOCODER_CLEANUP_TIMEOUT: Cleanup timeout in seconds
            AUTOCODER_GRACE_PERIOD: Grace period in seconds
            
        Returns:
            TimeoutConfig instance configured from environment
        """
        def get_optional_float(env_var: str, default: Optional[float]) -> Optional[float]:
            value = os.getenv(env_var)
            if value is None:
                return default
            if value.lower() in ('none', 'null', ''):
                return None
            try:
                return float(value)
            except ValueError:
                raise TimeoutConfigError(
                    env_var, 
                    value, 
                    "must be a valid number or 'none'"
                )
        
        def get_float(env_var: str, default: float) -> float:
            value = os.getenv(env_var)
            if value is None:
                return default
            try:
                return float(value)
            except ValueError:
                raise TimeoutConfigError(
                    env_var, 
                    value, 
                    "must be a valid number"
                )
        
        return cls(
            default_timeout=get_optional_float('AUTOCODER_DEFAULT_TIMEOUT', 300.0),
            interactive_timeout=get_optional_float('AUTOCODER_INTERACTIVE_TIMEOUT', 600.0),
            cleanup_timeout=get_float('AUTOCODER_CLEANUP_TIMEOUT', 10.0),
            grace_period=get_float('AUTOCODER_GRACE_PERIOD', 5.0),
        )
    
    def to_dict(self) -> Dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            'default_timeout': self.default_timeout,
            'interactive_timeout': self.interactive_timeout,
            'cleanup_timeout': self.cleanup_timeout,
            'grace_period': self.grace_period,
            'command_timeouts': self.command_timeouts.copy(),
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'TimeoutConfig':
        """
        Create TimeoutConfig from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            TimeoutConfig instance
        """
        return cls(
            default_timeout=config_dict.get('default_timeout', 300.0),
            interactive_timeout=config_dict.get('interactive_timeout', 600.0),
            cleanup_timeout=config_dict.get('cleanup_timeout', 10.0),
            grace_period=config_dict.get('grace_period', 5.0),
            command_timeouts=config_dict.get('command_timeouts', {}),
        )
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"TimeoutConfig("
            f"default={self.default_timeout}, "
            f"interactive={self.interactive_timeout}, "
            f"cleanup={self.cleanup_timeout}, "
            f"grace={self.grace_period}, "
            f"overrides={len(self.command_timeouts)})"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"TimeoutConfig("
            f"default_timeout={self.default_timeout}, "
            f"interactive_timeout={self.interactive_timeout}, "
            f"cleanup_timeout={self.cleanup_timeout}, "
            f"grace_period={self.grace_period}, "
            f"command_timeouts={self.command_timeouts})"
        ) 