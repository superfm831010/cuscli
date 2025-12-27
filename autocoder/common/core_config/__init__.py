"""
Core Config Module

Provides centralized configuration and memory management for auto-coder.

This module has been refactored into multiple specialized modules for better
maintainability and separation of concerns:

- models.py: Core data structures
- base_manager.py: Base persistence functionality  
- config_manager.py: Configuration management
- file_manager.py: File and file group management
- exclude_manager.py: Exclude patterns management
- lib_manager.py: Library management
- conversation_manager.py: Conversation management
- mode_manager.py: Mode management functionality
- human_as_model_manager.py: Human as model configuration management
- main_manager.py: Combined MemoryManager class
- compatibility.py: Backward compatibility functions
"""

# Import core classes and functions
from .models import CoreMemory
from .main_manager import MemoryManager, get_memory_manager, get_global_memory_manager
from .compatibility import (
    save_memory,
    save_memory_with_new_memory,
    load_memory,
    get_memory,
    get_mode,
    set_mode,
    cycle_mode,
    get_human_as_model,
    set_human_as_model,
    toggle_human_as_model,
    get_human_as_model_string,
    get_agentic_mode,
    set_agentic_mode,
    toggle_agentic_mode,
    get_agentic_mode_string,
)

# Export all public interfaces
__all__ = [
    'MemoryManager',
    'CoreMemory', 
    'get_memory_manager',
    'get_global_memory_manager',
    'save_memory',
    'save_memory_with_new_memory',
    'load_memory',
    'get_memory',
    'get_mode',
    'set_mode',
    'cycle_mode',
    'get_human_as_model',
    'set_human_as_model',
    'toggle_human_as_model',
    'get_human_as_model_string',
    'get_agentic_mode',
    'set_agentic_mode',
    'toggle_agentic_mode',
    'get_agentic_mode_string',
]
