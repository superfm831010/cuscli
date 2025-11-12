"""
Mode management functionality.

This module provides mode management methods for auto-coder sessions,
including mode setting, getting, and cycling functionality.
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CoreMemory


class ModeManagerMixin:
    """Mixin class providing mode management functionality."""
    
    # Available modes in cycle order
    MODE_CYCLE = ["normal", "auto_detect", "voice_input", "shell"]
    DEFAULT_MODE = "normal"
    
    # These will be provided by BaseMemoryManager when mixed in
    _memory: 'CoreMemory'
    
    def save_memory(self) -> None:
        """Save memory - provided by BaseMemoryManager."""
        ...
    
    def get_mode(self) -> str:
        """
        Get current operation mode.
        
        Returns:
            Current mode string, defaults to "normal" if not set
        """
        mode = self._memory.mode
        if not mode or mode not in self.MODE_CYCLE:
            mode = self.DEFAULT_MODE
            self.set_mode(mode)
        return mode
    
    def set_mode(self, mode: str):
        """
        Set operation mode.
        
        Args:
            mode: Mode to set (normal, auto_detect, voice_input, shell)
        """
        if mode not in self.MODE_CYCLE:
            raise ValueError(f"Invalid mode: {mode}. Valid modes: {self.MODE_CYCLE}")
        
        self._memory.mode = mode
        self.save_memory()
    
    def cycle_mode(self) -> str:
        """
        Cycle to next mode in sequence: normal -> auto_detect -> voice_input -> shell -> normal.
        
        Returns:
            New mode after cycling
        """
        current_mode = self.get_mode()
        
        try:
            current_index = self.MODE_CYCLE.index(current_mode)
            next_index = (current_index + 1) % len(self.MODE_CYCLE)
            new_mode = self.MODE_CYCLE[next_index]
        except ValueError:
            # If current mode is not in cycle, default to first mode
            new_mode = self.MODE_CYCLE[0]
        
        self.set_mode(new_mode)
        return new_mode
    
    def is_mode(self, mode: str) -> bool:
        """
        Check if current mode matches the specified mode.
        
        Args:
            mode: Mode to check against
            
        Returns:
            True if current mode matches, False otherwise
        """
        return self.get_mode() == mode
    
    def is_auto_detect_mode(self) -> bool:
        """Check if current mode is auto_detect."""
        return self.is_mode("auto_detect")
    
    def is_voice_input_mode(self) -> bool:
        """Check if current mode is voice_input."""
        return self.is_mode("voice_input")
    
    def is_normal_mode(self) -> bool:
        """Check if current mode is normal."""
        return self.is_mode("normal")
    
    def is_shell_mode(self) -> bool:
        """Check if current mode is shell."""
        return self.is_mode("shell")
    
    def get_available_modes(self) -> List[str]:
        """
        Get list of available modes.
        
        Returns:
            List of available mode strings
        """
        return self.MODE_CYCLE.copy()
    
    def reset_mode_to_default(self):
        """Reset mode to default value."""
        self.set_mode(self.DEFAULT_MODE)
    
    def ensure_mode_valid(self):
        """
        Ensure current mode is valid, reset to default if not.
        
        Returns:
            Current mode after validation
        """
        current_mode = self._memory.mode
        if not current_mode or current_mode not in self.MODE_CYCLE:
            self.reset_mode_to_default()
            return self.DEFAULT_MODE
        return current_mode 