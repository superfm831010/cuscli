"""
Hook executor for command execution with variable substitution and process management.
"""

import asyncio
import json
import os
import re
import shlex
import subprocess
import time
from typing import Dict, List, Optional, Any

from loguru import logger
from autocoder.common.async_utils import AsyncSyncMixin
from ..agent_events.types import EventMessage
from .types import Hook, HookExecutionResult, HookType


class HookExecutor(AsyncSyncMixin):
    """
    Command execution engine with variable substitution and environment control.
    
    Provides both async and sync methods for all operations.
    Sync methods are automatically generated with a '_sync' suffix.
    """
    
    def __init__(self, cwd: Optional[str] = None, timeout: int = 30000, 
                 env: Optional[Dict[str, str]] = None):
        """
        Initialize the hook executor.
        
        Args:
            cwd: Working directory for command execution
            timeout: Command timeout in milliseconds
            env: Additional environment variables
        """
        self.cwd = cwd or os.getcwd()
        self.timeout = timeout / 1000.0  # Convert to seconds
        self.env = env or {}
    
    def set_cwd(self, cwd: str) -> None:
        """Set working directory for command execution."""
        self.cwd = cwd
    
    def set_timeout(self, timeout: int) -> None:
        """Set command execution timeout in milliseconds."""
        self.timeout = timeout / 1000.0
    
    def set_env(self, env: Dict[str, str]) -> None:
        """Set environment variables."""
        self.env = env
    
    async def execute_hooks(self, hooks: List[Hook], event_message: EventMessage) -> List[HookExecutionResult]:
        """
        Execute all hooks in an array.
        
        Args:
            hooks: List of hooks to execute
            event_message: Event message for variable substitution
            
        Returns:
            List of execution results
        """
        results = []
        for hook in hooks:
            result = await self.execute_hook(hook, event_message)
            results.append(result)
        return results
    
    async def execute_hook(self, hook: Hook, event_message: EventMessage) -> HookExecutionResult:
        """
        Execute a single hook.
        
        Args:
            hook: Hook to execute
            event_message: Event message for variable substitution
            
        Returns:
            Execution result
        """
        if hook.type != HookType.COMMAND:
            return HookExecutionResult(
                success=False,
                command=hook.command,
                error_message=f"Unsupported hook type: {hook.type}"
            )
        
        # Process command variables
        processed_command = self._substitute_variables(hook.command, event_message)
        
        # Execute command
        return await self._execute_command(processed_command)
    
    def _substitute_variables(self, command: str, event_message: EventMessage) -> str:
        """
        Replace template variables in commands with runtime values.
        
        Supported variables:
        - {{event_type}}: The event type
        - {{event_id}}: The event ID
        - {{timestamp}}: The event timestamp
        - {{tool_name}}: The tool name from event content
        - {{event_content}}: Full event content as JSON
        - {{agent_id}}: Agent ID from context (if available)
        - {{conversation_id}}: Conversation ID from context (if available)
        - {{context_*}}: Context metadata fields
        - {{tool_*}}: Tool input fields
        
        Args:
            command: Command template with {{variable}} placeholders
            event_message: Event message containing variable values
            
        Returns:
            Command with variables substituted
        """
        variables = {
            'event_type': event_message.event_type.value,
            'event_id': event_message.event_id,
            'timestamp': str(event_message.timestamp),
            'tool_name': event_message.content.get('tool_name', ''),
            'event_content': json.dumps(event_message.content),
            'cwd': self.cwd
        }
        
        # Add context variables if available
        if event_message.context:
            if event_message.context.agent_id:
                variables['agent_id'] = event_message.context.agent_id
            if event_message.context.conversation_id:
                variables['conversation_id'] = event_message.context.conversation_id
            if event_message.context.metadata:
                for key, value in event_message.context.metadata.items():
                    variables[f'context_{key}'] = str(value)
        
        # Add tool-specific variables
        if 'tool_input' in event_message.content:
            tool_input = event_message.content['tool_input']
            if isinstance(tool_input, dict):
                for key, value in tool_input.items():
                    variables[f'tool_{key}'] = str(value)
        
        # Add additional content fields
        for key, value in event_message.content.items():
            if key not in ['tool_name', 'tool_input'] and isinstance(value, (str, int, float, bool)):
                variables[key] = str(value)
        
        # Substitute variables using regex
        def replace_var(match):
            var_name = match.group(1)
            return variables.get(var_name, match.group(0))
        
        # Replace {{variable}} patterns
        result = re.sub(r'\{\{(\w+)\}\}', replace_var, command)
        return result
    
    async def _execute_command(self, command: str) -> HookExecutionResult:
        """
        Execute shell command with timeout and error handling.
        
        Args:
            command: Command to execute
            
        Returns:
            Execution result with output, exit code, and timing
        """
        start_time = time.time()
        result = HookExecutionResult(
            success=False,
            command=command,
            start_time=start_time
        )
        
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            exec_env.update(self.env)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                env=exec_env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                # Update result
                result.stdout = stdout.decode('utf-8', errors='replace')
                result.stderr = stderr.decode('utf-8', errors='replace')
                result.exit_code = process.returncode
                result.success = process.returncode == 0
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                result.error_message = f"Command timed out after {self.timeout}s"
                result.exit_code = -1
        
        except Exception as e:
            result.error_message = str(e)
            result.exit_code = -1
            logger.error(f"Error executing command '{command}': {e}")
        
        finally:
            end_time = time.time()
            result.end_time = end_time
            result.execution_time = end_time - start_time
        
        return result 