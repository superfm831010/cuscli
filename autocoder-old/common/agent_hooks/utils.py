"""
Utility functions for the Agent Hooks system.
"""

import os
from typing import Dict, Optional, Any
from ..agent_events.types import EventMessage
from .types import HookProcessingResult
from .hook_manager import HookManager
from .hook_executor import HookExecutor

async def process_event(event_message: EventMessage, 
                       config_path: Optional[str] = None,
                       cwd: Optional[str] = None,
                       command_timeout: int = 30000) -> HookProcessingResult:
    """
    Convenience function to process an event with default configuration.
    
    Args:
        event_message: The event to process
        config_path: Path to hooks configuration file
        cwd: Working directory for command execution
        command_timeout: Command timeout in milliseconds
        
    Returns:
        HookProcessingResult with execution results
    """
    manager = HookManager(
        config_path=config_path,
        cwd=cwd,
        command_timeout=command_timeout
    )
    return await manager.process_event(event_message)

def create_hook_executor(cwd: Optional[str] = None, 
                        timeout: int = 30000,
                        env: Optional[Dict[str, str]] = None) -> HookExecutor:
    """
    Create a hook executor with the specified configuration.
    
    Args:
        cwd: Working directory for command execution
        timeout: Command timeout in milliseconds
        env: Environment variables
        
    Returns:
        Configured HookExecutor instance
    """
    return HookExecutor(cwd=cwd, timeout=timeout, env=env)

def create_hook_manager(config_path: Optional[str] = None,
                       cwd: Optional[str] = None,
                       command_timeout: int = 30000) -> HookManager:
    """
    Create a hook manager with the specified configuration.
    
    Args:
        config_path: Path to hooks configuration file
        cwd: Working directory for command execution
        command_timeout: Command timeout in milliseconds
        
    Returns:
        Configured HookManager instance
    """
    return HookManager(
        config_path=config_path,
        cwd=cwd,
        command_timeout=command_timeout
    )

def config_exists(config_path: Optional[str] = None) -> bool:
    """
    Check if hooks configuration file exists.
    Supports auto-detection of JSON and YAML formats.
    
    Args:
        config_path: Path to hooks configuration file
        
    Returns:
        True if configuration file exists, False otherwise
    """
    if config_path is None:
        # Auto-detect configuration file
        base_dir = os.path.join(os.getcwd(), '.auto-coder')
        
        # Check for configuration files in priority order
        candidates = [
            os.path.join(base_dir, 'hooks.json'),
            os.path.join(base_dir, 'hooks.yaml'),
            os.path.join(base_dir, 'hooks.yml')
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return True
        
        return False
    else:
        return os.path.exists(config_path) 