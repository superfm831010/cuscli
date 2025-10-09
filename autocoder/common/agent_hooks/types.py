"""
Type definitions for the Agent Hooks system.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

class HookType(str, Enum):
    """Types of hooks supported by the system."""
    COMMAND = "command"

@dataclass
class Hook:
    """Individual hook definition with type and command."""
    type: HookType
    command: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hook to dictionary."""
        result = {
            'type': self.type.value,
            'command': self.command
        }
        if self.description:
            result['description'] = self.description
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hook':
        """Create hook from dictionary."""
        return cls(
            type=HookType(data.get('type', HookType.COMMAND.value)),
            command=data.get('command', ''),
            description=data.get('description')
        )

@dataclass 
class HookMatcher:
    """Pattern matching and hook configuration."""
    matcher: str  # Regular expression pattern
    hooks: List[Hook] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hook matcher to dictionary."""
        return {
            'matcher': self.matcher,
            'hooks': [hook.to_dict() for hook in self.hooks]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HookMatcher':
        """Create hook matcher from dictionary."""
        hooks = []
        for hook_data in data.get('hooks', []):
            hooks.append(Hook.from_dict(hook_data))
        
        return cls(
            matcher=data.get('matcher', ''),
            hooks=hooks
        )

@dataclass
class HooksConfig:
    """Complete configuration structure with event type mapping."""
    hooks: Dict[str, List[HookMatcher]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hooks config to dictionary."""
        result = {}
        for event_type, matchers in self.hooks.items():
            result[event_type] = [matcher.to_dict() for matcher in matchers]
        return {'hooks': result}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HooksConfig':
        """Create hooks config from dictionary."""
        hooks = {}
        hooks_data = data.get('hooks', {})
        
        for event_type, matchers_data in hooks_data.items():
            matchers = []
            for matcher_data in matchers_data:
                matchers.append(HookMatcher.from_dict(matcher_data))
            hooks[event_type] = matchers
        
        return cls(hooks=hooks)

@dataclass
class HookExecutionResult:
    """Command execution results and metrics."""
    success: bool
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution result to dictionary."""
        return {
            'success': self.success,
            'command': self.command,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'execution_time': self.execution_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'error_message': self.error_message
        }

@dataclass
class HookProcessingResult:
    """Overall event processing results."""
    matched: bool
    results: List[HookExecutionResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert processing result to dictionary."""
        return {
            'matched': self.matched,
            'results': [result.to_dict() for result in self.results],
            'errors': self.errors,
            'processing_time': self.processing_time
        } 