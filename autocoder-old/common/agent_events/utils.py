"""
Utility functions for the Agent Events system.
"""

from typing import Dict, Any, Optional, Tuple
from .types import EventMessage, EventType, EventContext, EventEmitterConfig
from .event_factory import EventFactory
from .agent_event_emitter import AgentEventEmitter

def create_event_system(config: Optional[EventEmitterConfig] = None) -> Tuple[AgentEventEmitter, EventFactory]:
    """
    Create a complete event system with emitter and factory.
    
    Returns:
        Tuple of (emitter, factory) ready to use
    """
    emitter = AgentEventEmitter(config)
    factory = EventFactory()
    return emitter, factory

def create_pre_tool_use_event(tool_name: str, tool_input: Dict[str, Any],
                             context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create a PreToolUse event."""
    factory = EventFactory()
    return factory.create_pre_tool_use_event(tool_name, tool_input, context)

def create_post_tool_use_event(tool_name: str, tool_input: Dict[str, Any],
                              tool_output: Any, success: bool, 
                              execution_time_ms: Optional[float] = None,
                              context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create a PostToolUse event."""
    factory = EventFactory()
    return factory.create_post_tool_use_event(
        tool_name, tool_input, tool_output, success, execution_time_ms, context
    )

def create_error_occurred_event(error_type: str, error_message: str,
                               tool_name: Optional[str] = None,
                               stack_trace: Optional[str] = None,
                               context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create an ErrorOccurred event."""
    factory = EventFactory()
    return factory.create_error_occurred_event(
        error_type, error_message, tool_name, stack_trace, context
    )

def create_conversation_start_event(message_count: int = 0,
                                   conversation_id: Optional[str] = None,
                                   context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create a ConversationStart event."""
    factory = EventFactory()
    return factory.create_conversation_start_event(message_count, conversation_id, context)

def create_conversation_end_event(did_complete_task: bool,
                                 iteration_count: int = 0,
                                 conversation_id: Optional[str] = None,
                                 context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create a ConversationEnd event."""
    factory = EventFactory()
    return factory.create_conversation_end_event(
        did_complete_task, iteration_count, conversation_id, context
    )

def create_custom_event(event_name: str, data: Dict[str, Any],
                       context: Optional[EventContext] = None) -> EventMessage:
    """Convenience function to create a custom event."""
    factory = EventFactory()
    return factory.create_custom_event(event_name, data, context) 