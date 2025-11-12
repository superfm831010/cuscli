"""
Hook manager for configuration loading, caching, and event processing.
"""

import asyncio
import json
import os
import re
import time
import yaml
from typing import Dict, List, Optional, Tuple

from loguru import logger
from autocoder.common.async_utils import AsyncSyncMixin
from ..agent_events.types import EventMessage
from .types import HooksConfig, HookMatcher, HookProcessingResult
from .hook_executor import HookExecutor


class HookManager(AsyncSyncMixin):
    """
    Core hook management and event processing.
    
    Provides both async and sync methods for all operations.
    Sync methods are automatically generated with a '_sync' suffix.
    """
    
    def __init__(self, config_path: Optional[str] = None, cwd: Optional[str] = None, 
                 command_timeout: int = 30000):
        """
        Initialize the hook manager.
        
        Args:
            config_path: Path to hooks configuration file (supports .json, .yaml, .yml formats)
            cwd: Working directory for command execution
            command_timeout: Command timeout in milliseconds
        """        
        self.cwd = cwd or os.getcwd()
        self.config_path = config_path or self._find_default_config_path()
        self.command_timeout = command_timeout
        
        self._config: Optional[HooksConfig] = None
        self._config_mtime: Optional[float] = None
        self._executor = HookExecutor(cwd=self.cwd, timeout=command_timeout)
        self._config_lock = asyncio.Lock()
    
    def _find_default_config_path(self) -> str:
        """
        Find the default configuration file by checking for hooks.json, hooks.yaml, hooks.yml.
        
        Returns:
            Path to the first found configuration file, defaults to hooks.json if none found
        """
        base_dir = os.path.join(self.cwd, '.auto-coder')
        
        # Priority order: .json first for backward compatibility, then .yaml, then .yml
        candidates = [
            os.path.join(base_dir, 'hooks.json'),
            os.path.join(base_dir, 'hooks.yaml'),
            os.path.join(base_dir, 'hooks.yml')
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        # Default to hooks.json for backward compatibility
        return candidates[0]
    
    def _get_config_format(self, config_path: str) -> str:
        """
        Detect configuration file format based on file extension.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            File format: 'json', 'yaml', or 'unknown'
        """
        ext = os.path.splitext(config_path)[1].lower()
        if ext == '.json':
            return 'json'
        elif ext in ['.yaml', '.yml']:
            return 'yaml'
        else:
            return 'unknown'
    
    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return os.path.exists(self.config_path)
    
    async def load_config(self) -> Dict[str, any]:
        """
        Load and validate hooks configuration from file.
        Supports both JSON and YAML formats.
        
        Returns:
            Dictionary with 'config' (HooksConfig or None) and 'errors' (list of error messages)
        """
        async with self._config_lock:
            errors = []
            config = None
            
            try:
                if not self.config_exists():
                    errors.append(f"Configuration file not found: {self.config_path}")
                    return {'config': None, 'errors': errors}
                
                # Check if we need to reload based on file modification time
                current_mtime = os.path.getmtime(self.config_path)
                if self._config is not None and self._config_mtime == current_mtime:
                    return {'config': self._config, 'errors': []}
                
                # Detect file format and load accordingly
                config_format = self._get_config_format(self.config_path)
                
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if config_format == 'json':
                        data = json.load(f)
                    elif config_format == 'yaml':
                        data = yaml.safe_load(f)
                    else:
                        errors.append(f"Unsupported configuration file format: {self.config_path}")
                        return {'config': None, 'errors': errors}
                
                # Validate configuration structure
                validation_errors = self._validate_config(data)
                if validation_errors:
                    errors.extend(validation_errors)
                    return {'config': None, 'errors': errors}
                
                # Create config object
                config = HooksConfig.from_dict(data)
                
                # Cache the configuration
                self._config = config
                self._config_mtime = current_mtime
                
                logger.info(f"Loaded hooks configuration from {self.config_path} (format: {config_format})")
                
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in configuration file: {e}")
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML in configuration file: {e}")
            except Exception as e:
                errors.append(f"Error loading configuration: {e}")
                logger.error(f"Failed to load hooks configuration: {e}")
            
            return {'config': config, 'errors': errors}
    
    def _validate_config(self, data: Dict) -> List[str]:
        """Validate configuration structure."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Configuration must be a JSON object")
            return errors
        
        if 'hooks' not in data:
            errors.append("Configuration must contain 'hooks' key")
            return errors
        
        hooks = data['hooks']
        if not isinstance(hooks, dict):
            errors.append("'hooks' must be an object")
            return errors
        
        # Validate each event type configuration
        for event_type, matchers in hooks.items():
            if not isinstance(matchers, list):
                errors.append(f"Event type '{event_type}' must have a list of matchers")
                continue
            
            for i, matcher in enumerate(matchers):
                if not isinstance(matcher, dict):
                    errors.append(f"Matcher {i} in '{event_type}' must be an object")
                    continue
                
                if 'matcher' not in matcher:
                    errors.append(f"Matcher {i} in '{event_type}' must have 'matcher' field")
                
                if 'hooks' not in matcher:
                    errors.append(f"Matcher {i} in '{event_type}' must have 'hooks' field")
                    continue
                
                hooks_list = matcher['hooks']
                if not isinstance(hooks_list, list):
                    errors.append(f"'hooks' in matcher {i} of '{event_type}' must be a list")
                    continue
                
                for j, hook in enumerate(hooks_list):
                    if not isinstance(hook, dict):
                        errors.append(f"Hook {j} in matcher {i} of '{event_type}' must be an object")
                        continue
                    
                    if 'type' not in hook:
                        errors.append(f"Hook {j} in matcher {i} of '{event_type}' must have 'type' field")
                    
                    if 'command' not in hook:
                        errors.append(f"Hook {j} in matcher {i} of '{event_type}' must have 'command' field")
        
        return errors
    
    async def process_event(self, event_message: EventMessage) -> HookProcessingResult:
        """
        Process an EventMessage and execute matching hooks.
        
        Args:
            event_message: The event to process
            
        Returns:
            HookProcessingResult containing execution results and any errors
        """
        start_time = time.time()
        result = HookProcessingResult(matched=False)
        
        try:
            # Load configuration
            load_result = await self.load_config()
            if load_result['errors']:
                result.errors.extend(load_result['errors'])
                return result
            
            config = load_result['config']
            if not config:
                result.errors.append("No configuration available")
                return result
            
            # Extract event type and tool name
            event_type = event_message.event_type.value
            tool_name = event_message.content.get('tool_name', '')
            
            # Find matching event type configuration
            if event_type not in config.hooks:
                logger.debug(f"No hooks configured for event type: {event_type}")
                return result  # No configuration for this event type
            
            matchers = config.hooks[event_type]
            
            # Process each matcher
            for matcher in matchers:
                try:
                    # Check if tool name matches the pattern
                    if re.search(matcher.matcher, tool_name):
                        result.matched = True
                        logger.info(f"Matched hook pattern '{matcher.matcher}' for tool '{tool_name}'")
                        
                        # Execute hooks for this matcher
                        execution_results = await self._executor.execute_hooks(matcher.hooks, event_message)
                        result.results.extend(execution_results)
                        
                        # Log execution summary
                        successful = sum(1 for r in execution_results if r.success)
                        failed = len(execution_results) - successful
                        logger.info(f"Executed {len(execution_results)} hooks: {successful} successful, {failed} failed")
                        
                except re.error as e:
                    error_msg = f"Invalid regex pattern '{matcher.matcher}': {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                except Exception as e:
                    error_msg = f"Error processing matcher '{matcher.matcher}': {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Error processing event: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        
        finally:
            result.processing_time = time.time() - start_time
            
            if result.matched:
                logger.info(f"Processed event {event_message.event_type.value} in {result.processing_time:.3f}s")
        
        return result
    
    async def reload_config(self) -> Dict[str, any]:
        """Force reload configuration from file."""
        async with self._config_lock:
            self._config = None
            self._config_mtime = None
        return await self.load_config()
    
    def get_current_config(self) -> Optional[HooksConfig]:
        """Get the currently loaded configuration."""
        return self._config 