"""
Agent Events Module

A comprehensive event handling system for auto-coder agents with support for 
event emission, subscription, filtering, and processing.
"""

from .types import (
    EventType,
    EventMessage,
    EventHandler,
    EventListener,
    EventMetrics,
    EventEmitterConfig,
    EventContext
)

from .event_factory import EventFactory
from .agent_event_emitter import AgentEventEmitter
from .utils import (
    create_event_system,
    create_pre_tool_use_event,
    create_post_tool_use_event,
    create_error_occurred_event,
    create_conversation_start_event,
    create_conversation_end_event,
    create_custom_event
)

__all__ = [
    # Types
    'EventType',
    'EventMessage', 
    'EventHandler',
    'EventListener',
    'EventMetrics',
    'EventEmitterConfig',
    'EventContext',
    
    # Core classes
    'EventFactory',
    'AgentEventEmitter',
    
    # Utility functions
    'create_event_system',
    'create_pre_tool_use_event',
    'create_post_tool_use_event', 
    'create_error_occurred_event',
    'create_conversation_start_event',
    'create_conversation_end_event',
    'create_custom_event'
] 