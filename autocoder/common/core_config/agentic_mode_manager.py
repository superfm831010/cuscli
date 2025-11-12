"""
Agentic Mode management functionality.

This module provides agentic_mode configuration management methods for auto-coder sessions,
including getting, setting, and toggling the agentic_mode between plan and act.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CoreMemory


class AgenticModeManagerMixin:
    """Mixin class providing agentic_mode management functionality."""
    
    # Available modes
    AGENTIC_MODES = ["plan", "act"]
    DEFAULT_AGENTIC_MODE = "act"
    
    # These will be provided by BaseMemoryManager when mixed in
    _memory: 'CoreMemory'
    
    def save_memory(self) -> None:
        """Save memory - provided by BaseMemoryManager."""
        ...
    
    def get_agentic_mode(self) -> str:
        """
        Get current agentic_mode status.
        
        Returns:
            Current agentic_mode ("plan" or "act"), defaults to "act"
        """
        # Ensure conf dict exists
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        # Get the value, defaulting to "act" if not set
        mode = self._memory.conf.get("agentic_mode", self.DEFAULT_AGENTIC_MODE)
        
        # Validate mode
        if mode not in self.AGENTIC_MODES:
            mode = self.DEFAULT_AGENTIC_MODE
            self._memory.conf["agentic_mode"] = mode
        
        return mode
    
    def set_agentic_mode(self, mode: str):
        """
        Set agentic_mode.
        
        Args:
            mode: Mode to set ("plan" or "act")
        """
        if mode not in self.AGENTIC_MODES:
            raise ValueError(f"Invalid agentic_mode: {mode}. Valid modes: {self.AGENTIC_MODES}")
        
        # Ensure conf dict exists
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        self._memory.conf["agentic_mode"] = mode
        self.save_memory()
    
    def toggle_agentic_mode(self) -> str:
        """
        Toggle agentic_mode between plan and act.
        
        Returns:
            New mode after toggling ("plan" or "act")
        """
        current_mode = self.get_agentic_mode()
        new_mode = "act" if current_mode == "plan" else "plan"
        self.set_agentic_mode(new_mode)
        return new_mode
    
    def is_agentic_plan_mode(self) -> bool:
        """Check if current agentic_mode is plan."""
        return self.get_agentic_mode() == "plan"
    
    def is_agentic_act_mode(self) -> bool:
        """Check if current agentic_mode is act."""
        return self.get_agentic_mode() == "act"
    
    def get_agentic_mode_string(self) -> str:
        """
        Get agentic_mode status as string for display.
        
        Returns:
            Current agentic_mode ("plan" or "act")
        """
        return self.get_agentic_mode()
    
    def ensure_agentic_mode_config(self):
        """
        Ensure agentic_mode configuration exists with default value.
        
        Returns:
            Current agentic_mode
        """
        if "conf" not in self._memory.__dict__ or self._memory.conf is None:
            self._memory.conf = {}
        
        if "agentic_mode" not in self._memory.conf:
            self._memory.conf["agentic_mode"] = self.DEFAULT_AGENTIC_MODE
            self.save_memory()
        
        return self.get_agentic_mode()
