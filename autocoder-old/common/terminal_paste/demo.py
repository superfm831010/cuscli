#!/usr/bin/env python3
"""Demo script for terminal_paste module functionality.

This script demonstrates how the terminal_paste module works:
1. Simulates paste events by saving content to files
2. Shows placeholder resolution
3. Demonstrates cleanup functionality
"""

import os
import sys
from autocoder.common.terminal_paste import (
    PasteManager, 
    resolve_paste_placeholders
)
from autocoder.common.terminal_paste.paste_handler import (
    cleanup_old_pastes,
    list_paste_files
)


def demo_basic_functionality():
    """Demonstrate basic paste functionality."""
    print("=== Terminal Paste Module Demo ===\n")
    
    # Initialize paste manager
    pm = PasteManager()
    print(f"Paste directory: {pm.paste_dir}")
    
    # Simulate saving some paste content
    print("\n1. Saving paste content...")
    content1 = """def hello_world():
    print("Hello, World!")
    return "success"
"""
    
    content2 = """# This is a markdown example
## Features
- Feature 1
- Feature 2
- Feature 3
"""
    
    file_id1 = pm.save_paste(content1)
    file_id2 = pm.save_paste(content2)
    
    print(f"   Saved Python code as: {file_id1}")
    print(f"   Saved Markdown as: {file_id2}")
    
    # Show placeholder resolution
    print("\n2. Demonstrating placeholder resolution...")
    test_command = f"/coding Please review this code: [{file_id1}] and update the documentation: [{file_id2}]"
    print(f"   Original command: {test_command}")
    
    resolved_command = resolve_paste_placeholders(test_command)
    print(f"   Resolved command: {resolved_command}")
    
    # List all paste files
    print("\n3. Listing all paste files...")
    paste_files = list_paste_files()
    for i, paste_file in enumerate(paste_files, 1):
        print(f"   {i}. {paste_file}")
    
    # Read back content
    print("\n4. Reading back content...")
    read_content1 = pm.read_paste(file_id1)
    print(f"   Content from {file_id1}:")
    if read_content1:
        print(f"   {repr(read_content1[:50])}...")
    else:
        print("   Content not found")
    
    # Cleanup demonstration
    print("\n5. Cleanup demonstration...")
    print(f"   Files before cleanup: {len(paste_files)}")
    cleaned_count = cleanup_old_pastes(max_age_hours=0)  # Clean all files
    print(f"   Files cleaned: {cleaned_count}")
    
    remaining_files = list_paste_files()
    print(f"   Files after cleanup: {len(remaining_files)}")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===\n")
    
    pm = PasteManager()
    
    # Try to read non-existent file
    print("1. Reading non-existent file...")
    non_existent = pm.read_paste("pasted-nonexistent12345")
    print(f"   Result: {non_existent}")
    
    # Try to resolve invalid placeholder
    print("\n2. Resolving invalid placeholder...")
    invalid_text = "Command with [pasted-invalidid] placeholder"
    resolved = resolve_paste_placeholders(invalid_text)
    print(f"   Original: {invalid_text}")
    print(f"   Resolved: {resolved}")


def demo_integration_example():
    """Show how this would integrate with chat_auto_coder.py."""
    print("\n=== Integration Example ===\n")
    
    # Simulate what happens in chat_auto_coder.py
    pm = PasteManager()
    
    # User pastes some content (simulated)
    pasted_content = """SELECT users.name, COUNT(orders.id) as order_count
FROM users 
LEFT JOIN orders ON users.id = orders.user_id 
WHERE users.created_at > '2023-01-01'
GROUP BY users.id, users.name
ORDER BY order_count DESC;"""
    
    # Save the paste (this would happen in the paste handler)
    file_id = pm.save_paste(pasted_content)
    print(f"User pastes SQL query, saved as: {file_id}")
    
    # User types command with placeholder (what they see in terminal)
    user_input = f"/coding Please optimize this SQL query: [{file_id}]"
    print(f"User types: {user_input}")
    
    # Before processing, resolve placeholders (happens in main loop)
    resolved_input = resolve_paste_placeholders(user_input)
    print(f"System processes: {resolved_input}")
    
    print("\nThis way, the user sees a clean command line, but the system gets the full content!")


if __name__ == "__main__":
    try:
        demo_basic_functionality()
        demo_error_handling()
        demo_integration_example()
        print("\n=== Demo Complete ===")
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 