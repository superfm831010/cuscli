"""
Examples and demonstrations for the Agent Events module.
"""

import asyncio
import time
from autocoder.common.agent_events import (
    create_event_system,
    create_pre_tool_use_event,
    create_post_tool_use_event,
    create_error_occurred_event,
    create_conversation_start_event,
    create_conversation_end_event,
    EventFactory,
    EventContext,
    EventType,
    EventEmitterConfig
)


async def basic_event_system_example():
    """Basic event system usage example."""
    print("=== Basic Event System Example ===")
    
    # Create event system
    config = EventEmitterConfig(enable_logging=True, max_listeners=50)
    emitter, factory = create_event_system(config)
    
    # Event handlers
    async def pre_tool_handler(event):
        print(f"⚡ Tool starting: {event.content['tool_name']}")
    
    async def post_tool_handler(event):
        status = '✅ success' if event.content['success'] else '❌ failed'
        print(f"🏁 Tool completed: {event.content['tool_name']} - {status}")
    
    # Register handlers
    emitter.on(EventType.PRE_TOOL_USE, pre_tool_handler)
    emitter.on(EventType.POST_TOOL_USE, post_tool_handler)
    
    # Emit some events
    await emitter.emit(create_pre_tool_use_event('read_file', {'path': 'config.json'}))
    await emitter.emit(create_post_tool_use_event('read_file', {'path': 'config.json'}, 'file content', True, 45))
    
    await emitter.emit(create_pre_tool_use_event('write_file', {'path': 'output.txt'}))
    await emitter.emit(create_post_tool_use_event('write_file', {'path': 'output.txt'}, None, False, 12))
    
    # Show metrics
    metrics = emitter.get_metrics()
    print(f"📊 Metrics: {metrics.total_events} events, {metrics.average_processing_time:.3f}s avg")


def sync_event_system_example():
    """Synchronous event system usage example."""
    print("\n=== Synchronous Event System Example ===")
    
    # Create event system
    config = EventEmitterConfig(enable_logging=False)
    emitter, factory = create_event_system(config)
    
    # Sync event handler (note: handlers are still async, but called synchronously)
    async def handler(event):
        print(f"📌 Sync handler: {event.content['tool_name']}")
    
    emitter.on(EventType.PRE_TOOL_USE, handler)
    
    # Use sync methods (automatically provided by AsyncSyncMixin)
    event1 = create_pre_tool_use_event('sync_tool', {'param': 'value'})
    emitter.emit_sync(event1)  # This runs the async emit in a sync context
    
    # Wait for event synchronously
    print("⏳ Waiting for event synchronously...")
    
    # Create a task that will emit an event after a delay
    def emit_delayed():
        import time
        time.sleep(0.5)
        emitter.emit_sync(create_pre_tool_use_event('delayed_tool', {}))
    
    import threading
    thread = threading.Thread(target=emit_delayed)
    thread.start()
    
    # Wait for the event (with timeout)
    result = emitter.wait_for_event_sync(EventType.PRE_TOOL_USE, timeout=2.0)
    if result:
        print(f"📨 Received event: {result.content['tool_name']}")
    
    thread.join()


async def conversation_lifecycle_example():
    """Conversation lifecycle events example."""
    print("\n=== Conversation Lifecycle Example ===")
    
    emitter, factory = create_event_system()
    
    # Lifecycle handler
    async def lifecycle_handler(event):
        event_type = event.event_type.value
        if event_type == 'conversation_start':
            print(f"🚀 Conversation started with {event.content['message_count']} messages")
        elif event_type == 'conversation_end':
            completed = '✅' if event.content['did_complete_task'] else '❌'
            print(f"🏁 Conversation ended {completed} after {event.content['iteration_count']} iterations")
    
    # Register for lifecycle events
    emitter.on(EventType.CONVERSATION_START, lifecycle_handler)
    emitter.on(EventType.CONVERSATION_END, lifecycle_handler)
    
    # Simulate conversation lifecycle
    await emitter.emit(create_conversation_start_event(0, 'conv-123'))
    await asyncio.sleep(0.1)  # Simulate work
    await emitter.emit(create_conversation_end_event(True, 5, 'conv-123'))


async def advanced_event_processing_example():
    """Advanced event processing with filtering and context."""
    print("\n=== Advanced Event Processing Example ===")
    
    emitter, factory = create_event_system()
    
    # Create factory with context
    context = EventContext(
        agent_id='agent-001',
        conversation_id='conv-456',
        metadata={'version': '1.0.0', 'environment': 'test'}
    )
    contextual_factory = EventFactory.create_with_context(context)
    
    # Filtered handlers
    async def success_handler(event):
        print(f"✅ Successful operation: {event.content['tool_name']}")
    
    async def failure_handler(event):
        print(f"❌ Failed operation: {event.content['tool_name']}")
        if 'error_message' in event.content:
            print(f"   Error: {event.content['error_message']}")
    
    async def context_handler(event):
        if event.context:
            print(f"🏷️  Agent: {event.context.agent_id}, Conv: {event.context.conversation_id}")
    
    # Add filtered listeners
    def success_filter(event):
        return event.content.get('success', False) == True
    
    def failure_filter(event):
        return event.content.get('success', False) == False
    
    emitter.add_listener(EventType.POST_TOOL_USE, success_handler, filter=success_filter)
    emitter.add_listener(EventType.POST_TOOL_USE, failure_handler, filter=failure_filter)
    emitter.add_listener(EventType.POST_TOOL_USE, context_handler)
    
    # One-time error handler
    async def critical_error_handler(event):
        print(f"🚨 CRITICAL ERROR: {event.content['error_message']}")
    
    emitter.add_listener(EventType.ERROR_OCCURRED, critical_error_handler, once=True)
    
    # Emit events with context
    success_event = contextual_factory.create_post_tool_use_event(
        'process_data', {'dataset': 'users.csv'}, {'processed': 1000}, True, 2500
    )
    await emitter.emit(success_event)
    
    failure_event = contextual_factory.create_post_tool_use_event(
        'validate_data', {'schema': 'user_schema'}, None, False, 100
    )
    await emitter.emit(failure_event)
    
    # Emit error (will trigger one-time handler)
    error_event = contextual_factory.create_error_occurred_event(
        'VALIDATION_ERROR', 'Required field missing', 'validate_data'
    )
    await emitter.emit(error_event)
    
    # Emit another error (one-time handler won't trigger)
    another_error = contextual_factory.create_error_occurred_event(
        'TIMEOUT_ERROR', 'Operation timed out', 'slow_operation'
    )
    await emitter.emit(another_error)


async def event_waiting_example():
    """Example of waiting for specific events."""
    print("\n=== Event Waiting Example ===")
    
    emitter, factory = create_event_system()
    
    # Background task that emits events
    async def background_task():
        await asyncio.sleep(1)
        await emitter.emit(create_pre_tool_use_event('background_task', {}))
        await asyncio.sleep(1)
        await emitter.emit(create_post_tool_use_event('background_task', {}, 'result', True, 500))
    
    # Start background task
    asyncio.create_task(background_task())
    
    # Wait for specific events
    print("⏳ Waiting for PreToolUse event...")
    pre_event = await emitter.wait_for_event(EventType.PRE_TOOL_USE, timeout=5.0)
    if pre_event:
        print(f"📨 Received PreToolUse: {pre_event.content['tool_name']}")
    
    print("⏳ Waiting for PostToolUse event...")
    post_event = await emitter.wait_for_event(EventType.POST_TOOL_USE, timeout=5.0)
    if post_event:
        print(f"📨 Received PostToolUse: {post_event.content['tool_name']}")
    
    # Wait for event that won't come (will timeout)
    print("⏳ Waiting for non-existent event (will timeout)...")
    timeout_event = await emitter.wait_for_event(EventType.ERROR_OCCURRED, timeout=1.0)
    if timeout_event is None:
        print("⏰ Event wait timed out as expected")


async def performance_test_example():
    """Performance testing example."""
    print("\n=== Performance Test Example ===")
    
    emitter, factory = create_event_system()
    
    # Simple handler
    async def fast_handler(event):
        pass  # Do nothing for performance test
    
    emitter.on(EventType.PRE_TOOL_USE, fast_handler)
    
    # Performance test
    num_events = 1000
    start_time = time.time()
    
    tasks = []
    for i in range(num_events):
        event = create_pre_tool_use_event(f'tool_{i}', {'index': i})
        tasks.append(emitter.emit(event))
    
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    metrics = emitter.get_metrics()
    print(f"🚀 Performance Results:")
    print(f"   Events processed: {metrics.total_events}")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Events/second: {num_events / total_time:.1f}")
    print(f"   Average processing time: {metrics.average_processing_time * 1000:.2f}ms")


def mixed_sync_async_example():
    """Example mixing sync and async usage."""
    print("\n=== Mixed Sync/Async Example ===")
    
    # Create event system
    emitter, factory = create_event_system()
    
    # Handler
    async def handler(event):
        print(f"🔄 Mixed handler: {event.event_type.value} - {event.content.get('tool_name', 'N/A')}")
    
    emitter.on(EventType.PRE_TOOL_USE, handler)
    emitter.on(EventType.POST_TOOL_USE, handler)
    
    # Use sync method from non-async context
    print("Using sync methods:")
    emitter.emit_sync(create_pre_tool_use_event('sync_tool', {}))
    
    # Get metrics synchronously
    metrics = emitter.get_metrics()
    print(f"Events so far: {metrics.total_events}")
    
    # Now switch to async context
    async def async_part():
        print("\nUsing async methods:")
        await emitter.emit(create_post_tool_use_event('async_tool', {}, 'result', True))
        
        # Can still use sync methods from async context if needed
        emitter.emit_sync(create_pre_tool_use_event('another_sync_tool', {}))
    
    # Run the async part
    asyncio.run(async_part())
    
    # Back to sync
    final_metrics = emitter.get_metrics()
    print(f"\nTotal events processed: {final_metrics.total_events}")


async def run_all_examples():
    """Run all examples."""
    print("🎭 Agent Events Module Examples\n")
    
    await basic_event_system_example()
    sync_event_system_example()
    await conversation_lifecycle_example()
    await advanced_event_processing_example()
    await event_waiting_example()
    await performance_test_example()
    mixed_sync_async_example()
    
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(run_all_examples()) 