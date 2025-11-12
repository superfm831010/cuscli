"""
Agent Hooks Module

An event-driven command execution system that processes EventMessage types and 
executes corresponding commands based on configuration.
"""

from .types import (
    HooksConfig,
    HookMatcher, 
    Hook,
    HookExecutionResult,
    HookProcessingResult,
    HookType
)

from .hook_manager import HookManager
from .hook_executor import HookExecutor
from .utils import (
    process_event,
    create_hook_executor,
    create_hook_manager,
    config_exists
)

__all__ = [
    # Types
    'HooksConfig',
    'HookMatcher',
    'Hook',
    'HookExecutionResult', 
    'HookProcessingResult',
    'HookType',
    
    # Core classes
    'HookManager',
    'HookExecutor',
    
    # Utility functions
    'process_event',
    'create_hook_executor',
    'create_hook_manager',
    'config_exists'
] 