#!/usr/bin/env python3
"""
Test cases for indented batch command formats to verify textwrap.dedent compatibility.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool
from autocoder.common.v2.agent.agentic_edit_tools.execute_command_tool_resolver import ExecuteCommandToolResolver
from autocoder.common import AutoCoderArgs


def test_indented_json_object():
    """Test JSON object format with overall indentation."""
    print("=== Testing Indented JSON Object Format ===")
    
    # Simulate indented JSON as it might appear in XML tags
    indented_json = """    {
        "mode": "serial",
        "cmds": [
            "echo 'Indented JSON Step 1'",
            "echo 'Indented JSON Step 2'",
            "echo 'Indented JSON Step 3'"
        ]
    }"""
    
    tool = ExecuteCommandTool(
        command=indented_json,
        requires_approval=False,
        timeout=30
    )
    
    args = AutoCoderArgs(
        source_dir='.',
        enable_agentic_dangerous_command_check=False,
        enable_agentic_auto_approve=True,
        use_shell_commands=True
    )
    
    resolver = ExecuteCommandToolResolver(None, tool, args)
    result = resolver.resolve()
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.content and 'summary' in result.content:
        summary = result.content['summary']
        print(f"Execution mode: {summary['execution_mode']}")
        print(f"Total commands: {summary['total']}")
        print(f"Successful: {summary['successful']}")
        print("Command outputs:")
        for i, r in enumerate(result.content['batch_results']):
            print(f"  {i+1}. {r['output'].strip()}")
    
    assert result.success, f"Indented JSON test failed: {result.message}"
    print("✓ Indented JSON object test passed\n")


def test_indented_yaml():
    """Test YAML format with overall indentation."""
    print("=== Testing Indented YAML Format ===")
    
    # Simulate indented YAML as it might appear in XML tags
    indented_yaml = """    mode: parallel
    cmds:
      - echo 'Indented YAML Task A'
      - echo 'Indented YAML Task B'
      - echo 'Indented YAML Task C'
    """
    
    tool = ExecuteCommandTool(
        command=indented_yaml,
        requires_approval=False,
        timeout=30
    )
    
    args = AutoCoderArgs(
        source_dir='.',
        enable_agentic_dangerous_command_check=False,
        enable_agentic_auto_approve=True,
        use_shell_commands=True
    )
    
    resolver = ExecuteCommandToolResolver(None, tool, args)
    result = resolver.resolve()
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.content and 'summary' in result.content:
        summary = result.content['summary']
        print(f"Execution mode: {summary['execution_mode']}")
        print(f"Total commands: {summary['total']}")
        print(f"Successful: {summary['successful']}")
        print("Command outputs:")
        for i, r in enumerate(result.content['batch_results']):
            print(f"  {i+1}. {r['output'].strip()}")
    
    assert result.success, f"Indented YAML test failed: {result.message}"
    print("✓ Indented YAML test passed\n")


def test_indented_multiline_text():
    """Test multiline text format with overall indentation."""
    print("=== Testing Indented Multiline Text Format ===")
    
    # Simulate indented multiline text as it might appear in XML tags
    indented_multiline = """    # parallel
    echo 'Indented Line 1'
    echo 'Indented Line 2'
    echo 'Indented Line 3'
    """
    
    tool = ExecuteCommandTool(
        command=indented_multiline,
        requires_approval=False,
        timeout=30
    )
    
    args = AutoCoderArgs(
        source_dir='.',
        enable_agentic_dangerous_command_check=False,
        enable_agentic_auto_approve=True,
        use_shell_commands=True
    )
    
    resolver = ExecuteCommandToolResolver(None, tool, args)
    result = resolver.resolve()
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.content and 'summary' in result.content:
        summary = result.content['summary']
        print(f"Execution mode: {summary['execution_mode']}")
        print(f"Total commands: {summary['total']}")
        print(f"Successful: {summary['successful']}")
        print("Command outputs:")
        for i, r in enumerate(result.content['batch_results']):
            print(f"  {i+1}. {r['output'].strip()}")
    
    assert result.success, f"Indented multiline test failed: {result.message}"
    print("✓ Indented multiline text test passed\n")


def test_mixed_indentation():
    """Test mixed indentation scenarios."""
    print("=== Testing Mixed Indentation Scenarios ===")
    
    # Test case with inconsistent indentation that should still work
    mixed_yaml = """        mode: serial
        cmds:
          - echo 'Mixed indentation test 1'
          - echo 'Mixed indentation test 2'
    """
    
    tool = ExecuteCommandTool(
        command=mixed_yaml,
        requires_approval=False,
        timeout=30
    )
    
    args = AutoCoderArgs(
        source_dir='.',
        enable_agentic_dangerous_command_check=False,
        enable_agentic_auto_approve=True,
        use_shell_commands=True
    )
    
    resolver = ExecuteCommandToolResolver(None, tool, args)
    result = resolver.resolve()
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.content and 'summary' in result.content:
        summary = result.content['summary']
        print(f"Execution mode: {summary['execution_mode']}")
        print(f"Total commands: {summary['total']}")
        print(f"Successful: {summary['successful']}")
    
    assert result.success, f"Mixed indentation test failed: {result.message}"
    print("✓ Mixed indentation test passed\n")


def test_commands_field_with_indentation():
    """Test 'commands' field with indentation."""
    print("=== Testing Indented 'commands' Field ===")
    
    # Test JSON object with 'commands' field instead of 'cmds'
    indented_commands_json = """    {
        "mode": "serial",
        "commands": [
            "echo 'Commands field test 1'",
            "echo 'Commands field test 2'"
        ]
    }"""
    
    tool = ExecuteCommandTool(
        command=indented_commands_json,
        requires_approval=False,
        timeout=30
    )
    
    args = AutoCoderArgs(
        source_dir='.',
        enable_agentic_dangerous_command_check=False,
        enable_agentic_auto_approve=True,
        use_shell_commands=True
    )
    
    resolver = ExecuteCommandToolResolver(None, tool, args)
    result = resolver.resolve()
    
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.content and 'summary' in result.content:
        summary = result.content['summary']
        print(f"Execution mode: {summary['execution_mode']}")
        print(f"Total commands: {summary['total']}")
        print(f"Successful: {summary['successful']}")
    
    assert result.success, f"Commands field test failed: {result.message}"
    print("✓ Commands field with indentation test passed\n")


if __name__ == "__main__":
    print("Running indented batch command format tests...\n")
    
    try:
        test_indented_json_object()
        test_indented_yaml()
        test_indented_multiline_text()
        test_mixed_indentation()
        test_commands_field_with_indentation()
        
        print("🎉 All indented batch command tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 