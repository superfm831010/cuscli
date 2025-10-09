"""
Human as Model management functionality.

This module provides human_as_model configuration management methods for auto-coder sessions,
including getting, setting, and toggling the human_as_model status.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CoreMemory


class HumanAsModelManagerMixin:
    """Mixin class providing human_as_model management functionality."""
    
    # These will be provided by BaseMemoryManager when mixed in
    _memory: 'CoreMemory'
    
    def save_memory(self) -> None:
        """Save memory - provided by BaseMemoryManager."""
        ...
    
    def get_human_as_model(self) -> bool:
        """
        Get current human_as_model status.
        
        Returns:
            True if human_as_model is enabled, False otherwise
        """
        # Ensure conf dict exists
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        # Get the value, defaulting to "false" if not set
        value = self._memory.conf.get("human_as_model", "false")
        
        # Handle both string and boolean values
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() == "true"
        else:
            # Convert other types to boolean
            return bool(value)
    
    def set_human_as_model(self, enabled: bool):
        """
        Set human_as_model status.
        
        Args:
            enabled: True to enable human_as_model, False to disable
        """
        # Ensure conf dict exists
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        self._memory.conf["human_as_model"] = "true" if enabled else "false"
        self.save_memory()
    
    def toggle_human_as_model(self) -> bool:
        """
        Toggle human_as_model status between enabled and disabled.
        
        Returns:
            New status after toggling (True if enabled, False if disabled)
        """
        current_status = self.get_human_as_model()
        new_status = not current_status
        self.set_human_as_model(new_status)
        return new_status
    
    def enable_human_as_model(self):
        """Enable human_as_model mode."""
        self.set_human_as_model(True)
    
    def disable_human_as_model(self):
        """Disable human_as_model mode."""
        self.set_human_as_model(False)
    
    def is_human_as_model_enabled(self) -> bool:
        """
        Check if human_as_model is currently enabled.
        
        Returns:
            True if human_as_model is enabled, False otherwise
        """
        return self.get_human_as_model()
    
    def get_human_as_model_string(self) -> str:
        """
        Get human_as_model status as string.
        
        Returns:
            "true" if enabled, "false" if disabled
        """
        return "true" if self.get_human_as_model() else "false"
    
    def set_human_as_model_from_string(self, value: str):
        """
        Set human_as_model status from string value.
        
        Args:
            value: String value ("true"/"false", "1"/"0", "yes"/"no", etc.)
        """
        # Convert various string representations to boolean
        if isinstance(value, str):
            value_lower = value.lower().strip()
            enabled = value_lower in ("true", "1", "yes", "on", "enable", "enabled")
        else:
            enabled = bool(value)
        
        self.set_human_as_model(enabled)
    
    def ensure_human_as_model_config(self):
        """
        Ensure human_as_model configuration exists with default value.
        
        Returns:
            Current human_as_model status
        """
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        if "human_as_model" not in self._memory.conf:
            self._memory.conf["human_as_model"] = "false"
            self.save_memory()
        
        return self.get_human_as_model() 