"""
Core event emitter for agent events with support for filtering, metrics, and error handling.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Callable
from loguru import logger

from autocoder.common.async_utils import AsyncSyncMixin, run_async_in_sync
from .types import (
    EventMessage, EventType, EventHandler, EventListener, 
    EventMetrics, EventEmitterConfig, EventFilter
)


class AgentEventEmitter(AsyncSyncMixin):
    """
    Core event emitter for agent events.
    
    Provides both async and sync methods for all operations.
    Sync methods are automatically generated with a '_sync' suffix.
    """
    
    def __init__(self, config: Optional[EventEmitterConfig] = None):
        """Initialize the event emitter."""
        self.config = config or EventEmitterConfig()
        self._listeners: Dict[EventType, List[EventListener]] = defaultdict(list)
        self._metrics = EventMetrics()
        self._lock = asyncio.Lock()
    
    def on(self, event_type: EventType, handler: EventHandler) -> None:
        """Register an event handler for the specified event type."""
        self.add_listener(event_type, handler)
    
    def once(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a one-time event handler."""
        self.add_listener(event_type, handler, once=True)
    
    def off(self, event_type: EventType, handler: EventHandler) -> bool:
        """Remove an event handler."""
        listeners = self._listeners.get(event_type, [])
        for i, listener in enumerate(listeners):
            if listener.handler == handler:
                del listeners[i]
                self._metrics.total_handlers -= 1
                return True
        return False
    
    def add_listener(self, event_type: EventType, handler: EventHandler,
                    filter: Optional[EventFilter] = None, once: bool = False) -> None:
        """Add an event listener with advanced options."""
        if len(self._listeners[event_type]) >= self.config.max_listeners:
            logger.warning(f"Max listeners ({self.config.max_listeners}) reached for {event_type}")
            return
        
        listener = EventListener(handler=handler, filter=filter, once=once)
        self._listeners[event_type].append(listener)
        self._metrics.total_handlers += 1
        
        if self.config.enable_logging:
            logger.info(f"Added listener for {event_type} (once={once}, filtered={filter is not None})")
    
    def remove_listener(self, event_type: EventType, handler: EventHandler) -> bool:
        """Remove a specific event listener."""
        return self.off(event_type, handler)
    
    def remove_all_listeners(self, event_type: Optional[EventType] = None) -> None:
        """Remove all listeners for a specific event type or all events."""
        if event_type:
            count = len(self._listeners.get(event_type, []))
            self._listeners[event_type] = []
            self._metrics.total_handlers -= count
        else:
            total_removed = sum(len(listeners) for listeners in self._listeners.values())
            self._listeners.clear()
            self._metrics.total_handlers -= total_removed
        
        if self.config.enable_logging:
            logger.info(f"Removed all listeners for {event_type or 'all events'}")
    
    def listener_count(self, event_type: EventType) -> int:
        """Get the number of listeners for an event type."""
        return len(self._listeners.get(event_type, []))
    
    async def emit(self, event_message: EventMessage) -> None:
        """Emit an event to all registered handlers."""
        start_time = time.time()
        event_type = event_message.event_type
        
        if self.config.enable_logging:
            logger.info(f"Emitting event: {event_type} ({event_message.event_id})")
        
        # Get listeners for this event type (copy to avoid modification during iteration)
        listeners = self._listeners.get(event_type, []).copy()
        
        # Track listeners to remove (once handlers)
        to_remove = []
        
        # Process each listener
        for listener in listeners:
            try:
                # Apply filter if present
                if listener.filter and not listener.filter(event_message):
                    continue
                
                # Execute handler
                await listener.handler(event_message)
                
                # Mark once handlers for removal
                if listener.once:
                    to_remove.append((event_type, listener))
                
            except Exception as e:
                self._metrics.error_count += 1
                error_msg = f"Error in event handler for {event_type}: {e}"
                logger.error(error_msg)
                
                if self.config.error_handler:
                    try:
                        self.config.error_handler(e, event_type)
                    except Exception as handler_error:
                        logger.error(f"Error in error handler: {handler_error}")
        
        # Remove once handlers
        async with self._lock:
            for event_type_remove, listener_remove in to_remove:
                try:
                    self._listeners[event_type_remove].remove(listener_remove)
                    self._metrics.total_handlers -= 1
                except ValueError:
                    pass  # Already removed
        
        # Process with hook manager if available
        if self.config.hook_manager:
            try:
                # Hook manager process_event is always async, so we await it
                await self.config.hook_manager.process_event(event_message)
            except Exception as e:
                logger.error(f"Error in hook manager: {e}")
        
        # Update metrics
        processing_time = time.time() - start_time
        self._metrics.total_events += 1
        self._metrics.total_processing_time += processing_time
        
        # Update handler count metrics
        event_type_str = event_type.value
        self._metrics.handler_counts[event_type_str] = self._metrics.handler_counts.get(event_type_str, 0) + len(listeners)
        
        if self.config.enable_logging:
            logger.info(f"Event {event_type} processed in {processing_time:.3f}s")
    
    # The emit_sync method is automatically provided by AsyncSyncMixin
    
    async def wait_for_event(self, event_type: EventType, timeout: Optional[float] = None,
                           filter: Optional[EventFilter] = None) -> Optional[EventMessage]:
        """Wait for a specific event to be emitted."""
        future = asyncio.Future()
        
        async def handler(event_message: EventMessage):
            if not future.done():
                future.set_result(event_message)
        
        # Add temporary listener
        self.add_listener(event_type, handler, filter=filter, once=True)
        
        try:
            if timeout:
                return await asyncio.wait_for(future, timeout=timeout)
            else:
                return await future
        except asyncio.TimeoutError:
            # Remove the listener if timeout occurs
            self.off(event_type, handler)
            return None
    
    def get_metrics(self) -> EventMetrics:
        """Get event processing metrics."""
        return self._metrics
    
    def reset_metrics(self) -> None:
        """Reset event processing metrics."""
        self._metrics = EventMetrics()
    
    def list_event_types(self) -> List[EventType]:
        """Get all event types that have listeners."""
        return list(self._listeners.keys())
    
    def get_listeners(self, event_type: EventType) -> List[EventListener]:
        """Get all listeners for a specific event type."""
        return self._listeners.get(event_type, []).copy() 