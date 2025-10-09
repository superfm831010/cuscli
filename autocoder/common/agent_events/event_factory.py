"""
Event Factory for creating typed events with proper context management.
"""

import time
from typing import Dict, Any, Optional
from .types import EventMessage, EventType, EventContext

class EventFactory:
    """Factory for creating typed events with context management."""
    
    def __init__(self, default_context: Optional[EventContext] = None):
        """Initialize factory with optional default context."""
        self.default_context = default_context
    
    @classmethod
    def create_with_context(cls, context: EventContext) -> 'EventFactory':
        """Create a factory with default context."""
        return cls(default_context=context)
    
    def set_default_context(self, context: EventContext) -> None:
        """Set default context for all events created by this factory."""
        self.default_context = context
    
    def _create_event(self, event_type: EventType, content: Dict[str, Any], 
                     context: Optional[EventContext] = None) -> EventMessage:
        """Create an event with proper context inheritance."""
        # Merge contexts - specific context overrides default
        final_context = self.default_context
        if context:
            if final_context:
                # Merge contexts
                final_context = EventContext(
                    agent_id=context.agent_id or final_context.agent_id,
                    conversation_id=context.conversation_id or final_context.conversation_id,
                    metadata={**(final_context.metadata or {}), **(context.metadata or {})}
                )
            else:
                final_context = context
        
        return EventMessage(
            event_type=event_type,
            content=content,
            context=final_context
        )
    
    def create_pre_tool_use_event(self, tool_name: str, tool_input: Dict[str, Any],
                                 context: Optional[EventContext] = None) -> EventMessage:
        """Create a PreToolUse event."""
        content = {
            'tool_name': tool_name,
            'tool_input': tool_input,
            'timestamp': time.time()
        }
        return self._create_event(EventType.PRE_TOOL_USE, content, context)
    
    def create_post_tool_use_event(self, tool_name: str, tool_input: Dict[str, Any],
                                  tool_output: Any, success: bool, 
                                  execution_time_ms: Optional[float] = None,
                                  context: Optional[EventContext] = None) -> EventMessage:
        """Create a PostToolUse event."""
        content = {
            'tool_name': tool_name,
            'tool_input': tool_input,
            'tool_output': tool_output,
            'success': success,
            'timestamp': time.time()
        }
        if execution_time_ms is not None:
            content['execution_time_ms'] = execution_time_ms
        
        return self._create_event(EventType.POST_TOOL_USE, content, context)
    
    def create_error_occurred_event(self, error_type: str, error_message: str,
                                   tool_name: Optional[str] = None,
                                   stack_trace: Optional[str] = None,
                                   context: Optional[EventContext] = None) -> EventMessage:
        """Create an ErrorOccurred event."""
        content = {
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': time.time()
        }
        if tool_name:
            content['tool_name'] = tool_name
        if stack_trace:
            content['stack_trace'] = stack_trace
            
        return self._create_event(EventType.ERROR_OCCURRED, content, context)
    
    def create_conversation_start_event(self, message_count: int = 0,
                                       conversation_id: Optional[str] = None,
                                       context: Optional[EventContext] = None) -> EventMessage:
        """Create a ConversationStart event."""
        content = {
            'message_count': message_count,
            'timestamp': time.time()
        }
        if conversation_id:
            content['conversation_id'] = conversation_id
            
        return self._create_event(EventType.CONVERSATION_START, content, context)
    
    def create_conversation_end_event(self, did_complete_task: bool,
                                     iteration_count: int = 0,
                                     conversation_id: Optional[str] = None,
                                     context: Optional[EventContext] = None) -> EventMessage:
        """Create a ConversationEnd event."""
        content = {
            'did_complete_task': did_complete_task,
            'iteration_count': iteration_count,
            'timestamp': time.time()
        }
        if conversation_id:
            content['conversation_id'] = conversation_id
            
        return self._create_event(EventType.CONVERSATION_END, content, context)
    
    def create_tool_execution_event(self, tool_name: str, progress: float = 0.0,
                                   status: str = "running",
                                   context: Optional[EventContext] = None) -> EventMessage:
        """Create a ToolExecution event."""
        content = {
            'tool_name': tool_name,
            'progress': progress,
            'status': status,
            'timestamp': time.time()
        }
        return self._create_event(EventType.TOOL_EXECUTION, content, context)
    
    def create_tool_request_approval_event(self, tool_name: str, 
                                          tool_input: Dict[str, Any],
                                          reason: str = "",
                                          context: Optional[EventContext] = None) -> EventMessage:
        """Create a ToolRequestApproval event."""
        content = {
            'tool_name': tool_name,
            'tool_input': tool_input,
            'reason': reason,
            'timestamp': time.time()
        }
        return self._create_event(EventType.TOOL_REQUEST_APPROVAL, content, context)
    
    def create_mode_change_event(self, old_mode: str, new_mode: str,
                                context: Optional[EventContext] = None) -> EventMessage:
        """Create a ModeChange event."""
        content = {
            'old_mode': old_mode,
            'new_mode': new_mode,
            'timestamp': time.time()
        }
        return self._create_event(EventType.MODE_CHANGE, content, context)
    
    def create_token_count_info_event(self, input_tokens: int, output_tokens: int,
                                     total_tokens: int, model: Optional[str] = None,
                                     context: Optional[EventContext] = None) -> EventMessage:
        """Create a TokenCountInfo event."""
        content = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'timestamp': time.time()
        }
        if model:
            content['model'] = model
            
        return self._create_event(EventType.TOKEN_COUNT_INFO, content, context)
    
    def create_custom_event(self, event_name: str, data: Dict[str, Any],
                           context: Optional[EventContext] = None) -> EventMessage:
        """Create a custom event."""
        content = {
            'event_name': event_name,
            'data': data,
            'timestamp': time.time()
        }
        return self._create_event(EventType.CUSTOM_EVENT, content, context) 