"""
Compatibility functions for backward compatibility.

This module provides functions that maintain compatibility with
existing code that uses the old memory management interface.
"""

import threading
from typing import Dict, Any, Optional, TYPE_CHECKING
from .main_manager import get_memory_manager

if TYPE_CHECKING:
    from .main_manager import MemoryManager

# Global instance cache for compatibility
_default_memory_manager: Optional['MemoryManager'] = None
_default_memory_manager_lock = threading.Lock()


def save_memory():
    """Save memory (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    _default_memory_manager.save_memory()


def save_memory_with_new_memory(new_memory: Dict[str, Any]):
    """Save new memory (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    _default_memory_manager.save_memory_with_new_memory(new_memory)


def load_memory() -> Dict[str, Any]:
    """Load memory (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_memory_dict()


def get_memory() -> Dict[str, Any]:
    """Get memory (compatibility function)."""
    return load_memory()


# Mode management compatibility functions
def get_mode() -> str:
    """Get current mode (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_mode()


def set_mode(mode: str):
    """Set mode (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    _default_memory_manager.set_mode(mode)


def cycle_mode() -> str:
    """Cycle mode (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.cycle_mode()


# Human as model management compatibility functions
def get_human_as_model() -> bool:
    """Get human_as_model status (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_human_as_model()


def set_human_as_model(enabled: bool):
    """Set human_as_model status (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    _default_memory_manager.set_human_as_model(enabled)


def toggle_human_as_model() -> bool:
    """Toggle human_as_model status (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.toggle_human_as_model()


def get_human_as_model_string() -> str:
    """Get human_as_model status as string (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_human_as_model_string()


# Agentic mode management compatibility functions
def get_agentic_mode() -> str:
    """Get agentic_mode status (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_agentic_mode()


def set_agentic_mode(mode: str):
    """Set agentic_mode (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    _default_memory_manager.set_agentic_mode(mode)


def toggle_agentic_mode() -> str:
    """Toggle agentic_mode (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.toggle_agentic_mode()


def get_agentic_mode_string() -> str:
    """Get agentic_mode status as string (compatibility function)."""
    global _default_memory_manager
    with _default_memory_manager_lock:
        if _default_memory_manager is None:
            _default_memory_manager = get_memory_manager()
    return _default_memory_manager.get_agentic_mode_string()
