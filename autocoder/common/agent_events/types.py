"""
Type definitions for the Agent Events system.
"""

import time
from typing import Dict, Any, Optional, Callable, Awaitable, List, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Event types supported by the system
class EventType(str, Enum):
    """Event types that can be emitted and handled."""
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    TOOL_EXECUTION = "tool_execution"
    TOOL_REQUEST_APPROVAL = "tool_request_approval"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    MODE_CHANGE = "mode_change"
    ERROR_OCCURRED = "error_occurred"
    TOKEN_COUNT_INFO = "token_count_info"
    REQUEST_API = "request_api"
    REQUEST_API_COMPLETED = "request_api_completed"
    REQUEST_API_ABORT = "request_api_abort"
    CUSTOM_EVENT = "custom_event"

@dataclass
class EventContext:
    """Context information that can be attached to events."""
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EventMessage:
    """Enhanced event message with context and timing information."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM_EVENT
    timestamp: float = field(default_factory=time.time)
    content: Dict[str, Any] = field(default_factory=dict)
    context: Optional[EventContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event message to dictionary."""
        result = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'content': self.content
        }
        if self.context:
            result['context'] = {
                'agent_id': self.context.agent_id,
                'conversation_id': self.context.conversation_id,
                'metadata': self.context.metadata or {}
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMessage':
        """Create event message from dictionary."""
        context = None
        if 'context' in data:
            ctx_data = data['context']
            context = EventContext(
                agent_id=ctx_data.get('agent_id'),
                conversation_id=ctx_data.get('conversation_id'),
                metadata=ctx_data.get('metadata', {})
            )
        
        return cls(
            event_id=data.get('event_id', str(uuid.uuid4())),
            event_type=EventType(data.get('event_type', EventType.CUSTOM_EVENT.value)),
            timestamp=data.get('timestamp', time.time()),
            content=data.get('content', {}),
            context=context
        )

# Type aliases for event handlers
EventHandler = Callable[[EventMessage], Awaitable[None]]
EventFilter = Callable[[EventMessage], bool]

@dataclass
class EventListener:
    """Configuration for an event listener."""
    handler: EventHandler
    filter: Optional[EventFilter] = None
    once: bool = False
    
@dataclass
class EventMetrics:
    """Metrics for event processing."""
    total_events: int = 0
    total_handlers: int = 0
    total_processing_time: float = 0.0
    error_count: int = 0
    handler_counts: Dict[str, int] = field(default_factory=dict)
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time per event."""
        if self.total_events == 0:
            return 0.0
        return self.total_processing_time / self.total_events

@dataclass
class EventEmitterConfig:
    """Configuration for the AgentEventEmitter."""
    enable_logging: bool = False
    max_listeners: int = 100
    error_handler: Optional[Callable[[Exception, EventType], None]] = None
    hook_manager: Optional[Any] = None  # Import cycle avoidance 