"""
Examples and demonstrations for the Agent Hooks module.
"""

import asyncio
import json
import os
import tempfile
from autocoder.common.agent_hooks import (
    HookManager,
    HookExecutor,
    process_event,
    create_hook_manager,
    config_exists
)
from autocoder.common.agent_events import EventMessage, EventType, EventContext


async def basic_hook_usage_example():
    """Basic hook usage example."""
    print("=== Basic Hook Usage Example ===")
    
    # Create temporary config file (JSON format)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "WriteToFile|ReplaceInFile",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'File processed: {{tool_name}} at {{timestamp}}'",
                                "description": "Log file operations"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        # Create hook manager
        manager = HookManager(config_path=config_path)
        
        # Create test event
        event = EventMessage(
            event_type=EventType.POST_TOOL_USE,
            content={
                'tool_name': 'WriteToFile',
                'file_path': 'example.py',
                'success': True
            }
        )
        
        # Process event
        result = await manager.process_event(event)
        
        print(f"Event processed: {result.matched}")
        print(f"Commands executed: {len(result.results)}")
        
        for i, exec_result in enumerate(result.results):
            print(f"  Command {i+1}: {exec_result.command}")
            print(f"  Success: {exec_result.success}")
            print(f"  Output: {exec_result.stdout.strip()}")
    
    finally:
        # Clean up
        os.unlink(config_path)


async def yaml_hook_usage_example():
    """YAML hook configuration usage example."""
    print("\n=== YAML Hook Usage Example ===")
    
    # Create temporary YAML config file with multiline commands
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_config = """
hooks:
  PostToolUse:
    - matcher: "WriteToFile|ReplaceInFile"
      hooks:
        - type: command
          command: |
            echo "YAML: File processed: {{tool_name}} at {{timestamp}}"
            echo "File path: {{tool_file_path}}"
            echo "Success: {{success}}"
          description: "Log file operations using YAML config with multiline"
    - matcher: "ExecuteCommand"
      hooks:
        - type: command
          command: |
            echo "YAML: Command executed: {{tool_name}}"
            echo "Agent: {{agent_id}}"
            echo "Timestamp: {{timestamp}}"
          description: "Log command executions with details"
  
  PreToolUse:
    - matcher: ".*"
      hooks:
        - type: command
          command: |
            echo "YAML: About to execute: {{tool_name}}"
            echo "Event type: {{event_type}}"
            echo "Current working directory: {{cwd}}"
          description: "Pre-execution logging with context"
"""
        f.write(yaml_config.strip())
        config_path = f.name
    
    try:
        # Create hook manager
        manager = HookManager(config_path=config_path)
        
        # Create test events
        events = [
            EventMessage(
                event_type=EventType.PRE_TOOL_USE,
                content={'tool_name': 'WriteToFile'}
            ),
            EventMessage(
                event_type=EventType.POST_TOOL_USE,
                content={
                    'tool_name': 'WriteToFile',
                    'file_path': 'example.py',
                    'success': True
                }
            ),
            EventMessage(
                event_type=EventType.POST_TOOL_USE,
                content={'tool_name': 'ExecuteCommand', 'success': True}
            )
        ]
        
        # Process events
        for i, event in enumerate(events):
            print(f"\n--- Processing Event {i+1}: {event.event_type.value} ---")
            result = await manager.process_event(event)
            
            print(f"Event processed: {result.matched}")
            if result.results:
                for exec_result in result.results:
                    print(f"  Output: {exec_result.stdout.strip()}")
    
    finally:
        # Clean up
        os.unlink(config_path)


def sync_hook_usage_example():
    """Synchronous hook usage example."""
    print("\n=== Synchronous Hook Usage Example ===")
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'SYNC: About to use {{tool_name}}'",
                                "description": "Log all tool usage"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        # Create hook manager
        manager = HookManager(config_path=config_path)
        
        # Create test event
        event = EventMessage(
            event_type=EventType.PRE_TOOL_USE,
            content={'tool_name': 'ExecuteCommand'}
        )
        
        # Process event synchronously (automatically provided by AsyncSyncMixin)
        result = manager.process_event_sync(event)
        
        print(f"Event processed synchronously: {result.matched}")
        if result.results:
            print(f"Output: {result.results[0].stdout.strip()}")
    
    finally:
        os.unlink(config_path)


async def variable_substitution_example():
    """Variable substitution in commands example."""
    print("\n=== Variable Substitution Example ===")
    
    # Create config with various variable substitutions
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'Event: {{event_type}}, Tool: {{tool_name}}, Time: {{timestamp}}'",
                                "description": "Basic variable substitution"
                            },
                            {
                                "type": "command", 
                                "command": "echo 'Event content: {{event_content}}'",
                                "description": "Full event content as JSON"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        manager = HookManager(config_path=config_path)
        
        # Create event with context
        context = EventContext(
            agent_id='agent-001',
            conversation_id='conv-456',
            metadata={'environment': 'test', 'version': '1.0'}
        )
        
        event = EventMessage(
            event_type=EventType.POST_TOOL_USE,
            content={
                'tool_name': 'process_data',
                'tool_input': {'file_path': '/tmp/data.csv', 'format': 'csv'},
                'success': True
            },
            context=context
        )
        
        result = await manager.process_event(event)
        
        print("Variable substitution results:")
        for i, exec_result in enumerate(result.results):
            print(f"\n  Command {i+1}:")
            print(f"    Original: {exec_result.command}")
            print(f"    Output: {exec_result.stdout.strip()}")
    
    finally:
        os.unlink(config_path)


async def hook_executor_example():
    """Direct hook executor usage example (both async and sync)."""
    print("\n=== Hook Executor Example ===")
    
    # Create executor with custom settings
    executor = HookExecutor(timeout=5000)  # 5 second timeout
    
    # Create test hooks
    from autocoder.common.agent_hooks.types import Hook, HookType
    
    hooks = [
        Hook(
            type=HookType.COMMAND,
            command="echo 'Hello from hook 1'",
            description="Simple echo command"
        ),
        Hook(
            type=HookType.COMMAND,
            command="echo 'Tool: {{tool_name}}, Success: {{success}}'",
            description="Command with variables"
        ),
        Hook(
            type=HookType.COMMAND,
            command="sleep 0.1 && echo 'Delayed response'",
            description="Command with delay"
        )
    ]
    
    # Create test event
    event = EventMessage(
        event_type=EventType.POST_TOOL_USE,
        content={
            'tool_name': 'ExecuteCommand',
            'success': True
        }
    )
    
    # Execute hooks asynchronously
    print("Async execution:")
    results = await executor.execute_hooks(hooks, event)
    
    for i, result in enumerate(results):
        print(f"\n  Hook {i+1}:")
        print(f"    Success: {result.success}")
        print(f"    Output: {result.stdout.strip()}")
    
    # Execute a single hook synchronously
    print("\n\nSync execution:")
    single_result = executor.execute_hook_sync(hooks[0], event)
    print(f"  Success: {single_result.success}")
    print(f"  Output: {single_result.stdout.strip()}")


async def multiple_matchers_example():
    """Example with multiple matchers and event types."""
    print("\n=== Multiple Matchers Example ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'PRE: About to execute {{tool_name}}'",
                                "description": "Log all pre-tool events"
                            }
                        ]
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "WriteToFile|ReplaceInFile|ACModWrite",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'POST: File operation completed: {{tool_name}}'",
                                "description": "Log file operations"
                            }
                        ]
                    },
                    {
                        "matcher": "ExecuteCommand",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'POST: Command executed'",
                                "description": "Log command executions"
                            }
                        ]
                    }
                ],
                "error_occurred": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'ERROR: {{error_message}}'",
                                "description": "Log all errors"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        manager = HookManager(config_path=config_path)
        
        # Test different event types
        events = [
            EventMessage(
                event_type=EventType.PRE_TOOL_USE,
                content={'tool_name': 'WriteToFile'}
            ),
            EventMessage(
                event_type=EventType.POST_TOOL_USE,
                content={'tool_name': 'WriteToFile', 'success': True}
            ),
            EventMessage(
                event_type=EventType.POST_TOOL_USE,
                content={'tool_name': 'ExecuteCommand', 'success': True}
            ),
            EventMessage(
                event_type=EventType.ERROR_OCCURRED,
                content={'error_message': 'File not found', 'tool_name': 'ReadFile'}
            )
        ]
        
        for i, event in enumerate(events):
            print(f"\n--- Processing Event {i+1}: {event.event_type.value} ---")
            result = await manager.process_event(event)
            
            if result.matched:
                for exec_result in result.results:
                    print(f"  Output: {exec_result.stdout.strip()}")
            else:
                print("  No matching hooks")
    
    finally:
        os.unlink(config_path)


async def convenience_function_example():
    """Example using convenience functions."""
    print("\n=== Convenience Functions Example ===")
    
    # Create config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "ExecuteCommand.*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'Convenience test: {{tool_name}}'",
                                "description": "Test convenience function"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        # Test config_exists function
        print(f"Config exists: {config_exists(config_path)}")
        
        # Use process_event convenience function
        event = EventMessage(
            event_type=EventType.POST_TOOL_USE,
            content={'tool_name': 'ExecuteCommand'}
        )
        
        result = await process_event(event, config_path=config_path)
        
        print(f"Event processed via convenience function: {result.matched}")
        if result.results:
            print(f"Output: {result.results[0].stdout.strip()}")
    
    finally:
        os.unlink(config_path)


def mixed_sync_async_hooks_example():
    """Example mixing sync and async hook usage."""
    print("\n=== Mixed Sync/Async Hooks Example ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'Mixed mode: {{tool_name}}'",
                                "description": "Test mixed sync/async"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        manager = HookManager(config_path=config_path)
        
        # Sync usage
        print("Sync processing:")
        event1 = EventMessage(
            event_type=EventType.POST_TOOL_USE,
            content={'tool_name': 'sync_tool'}
        )
        result1 = manager.process_event_sync(event1)
        print(f"  Matched: {result1.matched}")
        if result1.results:
            print(f"  Output: {result1.results[0].stdout.strip()}")
        
        # Async usage within sync context (cannot use asyncio.run within async context)
        print("\nAsync processing (skipped in example - cannot nest asyncio.run)")
        print("  In real usage, you would call await manager.process_event(event) directly")
        
        # Back to sync
        print("\nBack to sync:")
        config_data = manager.load_config_sync()
        print(f"  Config loaded: {'success' if not config_data['errors'] else 'failed'}")
    
    finally:
        os.unlink(config_path)


async def error_handling_example():
    """Example demonstrating error handling."""
    print("\n=== Error Handling Example ===")
    
    # Test with invalid config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Invalid JSON
        f.write('{ "hooks": { "invalid": }')
        invalid_config_path = f.name
    
    try:
        manager = HookManager(config_path=invalid_config_path)
        load_result = await manager.load_config()
        
        print("Config loading errors:")
        for error in load_result['errors']:
            print(f"  - {error}")
    
    finally:
        os.unlink(invalid_config_path)
    
    # Test with command that fails
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "exit 1",  # This will fail
                                "description": "Failing command"
                            }
                        ]
                    }
                ]
            }
        }
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        event = EventMessage(
            event_type=EventType.POST_TOOL_USE,
            content={'tool_name': 'ExecuteCommand'}
        )
        
        result = await process_event(event, config_path=config_path)
        
        print("\nCommand execution results:")
        for exec_result in result.results:
            print(f"  Command: {exec_result.command}")
            print(f"  Success: {exec_result.success}")
            print(f"  Exit code: {exec_result.exit_code}")
    
    finally:
        os.unlink(config_path)


async def run_all_examples():
    """Run all examples."""
    print("🎣 Agent Hooks Module Examples\n")
    
    await basic_hook_usage_example()
    await yaml_hook_usage_example()
    sync_hook_usage_example()
    await variable_substitution_example()
    await hook_executor_example()
    await multiple_matchers_example()
    await convenience_function_example()
    mixed_sync_async_hooks_example()
    await error_handling_example()
    
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(run_all_examples()) 