"""
Example usage and demonstrations for the agents module.

This file provides practical examples of how to use the AgentManager and AgentParser.
"""

import os
import tempfile
from pathlib import Path
from autocoder.common.agents import AgentManager, AgentParser, Agent


def example_create_sample_agents():
    """Example: Create sample agent files for testing."""
    print("=== Creating Sample Agent Files ===")
    
    # Create a temporary directory for our example
    temp_dir = Path(tempfile.mkdtemp())
    agents_dir = temp_dir / ".autocoderagents"
    agents_dir.mkdir()
    
    # Sample agent definitions
    code_reviewer_agent = """---
name: code-reviewer
description: Expert code reviewer specializing in best practices and security
tools: read_file, write_to_file, search_files
model: gpt-4
include_rules: true
---

You are an expert code reviewer with extensive experience in software development.
Your role is to:

1. Review code for best practices, security vulnerabilities, and performance issues
2. Suggest improvements and optimizations
3. Ensure code follows established patterns and conventions
4. Check for proper error handling and edge cases

When reviewing code, focus on:
- Code quality and maintainability
- Security vulnerabilities
- Performance implications
- Best practices for the specific language/framework
- Documentation and testing coverage
"""

    documentation_agent = """---
name: documentation-writer
description: Technical documentation specialist for creating clear and comprehensive docs
tools: read_file, write_to_file, search_files
model: gpt-3.5-turbo
---

You are a technical documentation specialist with expertise in creating clear, 
comprehensive, and user-friendly documentation.

Your responsibilities include:
1. Writing clear API documentation
2. Creating user guides and tutorials
3. Documenting code architecture and design decisions
4. Ensuring documentation is up-to-date and accurate

Focus on:
- Clarity and readability
- Comprehensive examples
- Proper formatting and structure
- Accessibility for different skill levels
"""

    testing_agent = """---
name: test-engineer
description: Testing specialist focused on comprehensive test coverage and quality assurance
tools: read_file, write_to_file, execute_command, search_files
include_rules: false
---

You are a testing engineer specializing in creating comprehensive test suites 
and ensuring high-quality software delivery.

Your expertise includes:
1. Unit testing and integration testing
2. Test-driven development (TDD)
3. Performance and load testing
4. Test automation and CI/CD integration

When creating tests, ensure:
- High test coverage
- Edge case handling
- Clear test documentation
- Maintainable test code
- Proper test data management
"""

    # Write the agent files
    (agents_dir / "code-reviewer.md").write_text(code_reviewer_agent)
    (agents_dir / "documentation-writer.md").write_text(documentation_agent)
    (agents_dir / "test-engineer.md").write_text(testing_agent)
    
    print(f"Created sample agents in: {agents_dir}")
    print("- code-reviewer.md")
    print("- documentation-writer.md")
    print("- test-engineer.md")
    
    return temp_dir


def example_basic_usage():
    """Example: Basic AgentManager usage."""
    print("\n=== Basic AgentManager Usage ===")
    
    # Create sample agents
    project_root = example_create_sample_agents()
    
    try:
        # Initialize AgentManager
        manager = AgentManager(str(project_root))
        
        # List all available agents
        print(f"Total agents loaded: {len(manager.list_agents())}")
        print(f"Agent names: {manager.get_agent_names()}")
        
        # Get a specific agent
        reviewer = manager.get_agent("code-reviewer")
        if reviewer:
            print(f"\nAgent: {reviewer.name}")
            print(f"Description: {reviewer.description}")
            print(f"Tools: {reviewer.tools}")
            print(f"Model: {reviewer.model}")
            print(f"Include Rules: {reviewer.include_rules}")
            print(f"Content preview: {reviewer.content[:100]}...")
        
        # Try to get a non-existent agent
        non_existent = manager.get_agent("non-existent-agent")
        print(f"\nNon-existent agent: {non_existent}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(project_root)


def example_agent_parser():
    """Example: Using AgentParser directly."""
    print("\n=== AgentParser Direct Usage ===")
    
    # Sample agent content
    agent_content = """---
name: example-agent
description: An example agent for demonstration
tools: read_file, write_to_file, search_files
model: gpt-4
include_rules: false
---

You are an example agent created for demonstration purposes.
Your task is to show how agent parsing works.

Key capabilities:
1. Parse YAML frontmatter
2. Extract agent metadata
3. Validate agent definitions
"""

    try:
        # Parse agent content
        agent = AgentParser.parse_agent_content(agent_content)
        
        print(f"Parsed agent: {agent.name}")
        print(f"Description: {agent.description}")
        print(f"Tools: {agent.tools}")
        print(f"Model: {agent.model}")
        print(f"Include Rules: {agent.include_rules}")
        
        # Validate the agent
        errors = AgentParser.validate_agent(agent)
        if errors:
            print(f"Validation errors: {errors}")
        else:
            print("Agent validation: PASSED")
        
        # Convert to dictionary
        agent_dict = agent.to_dict()
        print(f"Agent as dict keys: {list(agent_dict.keys())}")
        
    except ValueError as e:
        print(f"Parsing error: {e}")


def example_validation_errors():
    """Example: Demonstrating validation errors."""
    print("\n=== Validation Error Examples ===")
    
    # Agent with missing required fields
    invalid_agent_content = """---
description: Agent without name field
tools: InvalidTool, Read
---

This agent is missing the name field and has an invalid tool.
"""

    try:
        agent = AgentParser.parse_agent_content(invalid_agent_content)
        errors = AgentParser.validate_agent(agent)
        
        if errors:
            print("Validation errors found:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        else:
            print("No validation errors (unexpected!)")
            
    except ValueError as e:
        print(f"Parsing failed as expected: {e}")


def example_priority_system():
    """Example: Demonstrating the priority system."""
    print("\n=== Agent Priority System Demo ===")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create agents in different priority directories
        high_priority_dir = temp_dir / ".autocoderagents"
        medium_priority_dir = temp_dir / ".auto-coder" / ".autocoderagents"
        
        high_priority_dir.mkdir()
        medium_priority_dir.mkdir(parents=True)
        
        # Same agent name in different directories
        high_priority_agent = """---
name: priority-test
description: High priority agent (should win)
model: gpt-4
---
This is the HIGH PRIORITY agent that should be loaded.
"""

        medium_priority_agent = """---
name: priority-test
description: Medium priority agent (should be overridden)
model: gpt-3.5-turbo
---
This is the medium priority agent that should be overridden.
"""

        # Write agents to different directories
        (high_priority_dir / "priority-test.md").write_text(high_priority_agent)
        (medium_priority_dir / "priority-test.md").write_text(medium_priority_agent)
        
        # Load agents using AgentManager
        manager = AgentManager(str(temp_dir))
        
        # Check which agent was loaded
        agent = manager.get_agent("priority-test")
        if agent:
            print(f"Loaded agent description: {agent.description}")
            print(f"Agent model: {agent.model}")
            print(f"Should be the HIGH PRIORITY agent")
        else:
            print("No agent loaded (unexpected)")
            
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def example_render_sub_agents():
    """Example: Rendering sub-agents section for system prompts."""
    print("\n=== Sub-Agents Section Rendering ===")
    
    project_root = example_create_sample_agents()
    
    try:
        manager = AgentManager(str(project_root))
        
        # Render sub-agents section
        result = manager.render_sub_agents_section(current_model="gpt-4")
        
        # The method returns a rendered template string
        if result and result.strip():
            print("Sub-agents section content:")
            print("-" * 50)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("-" * 50)
        else:
            print("No agents available for rendering")
            
    finally:
        import shutil
        shutil.rmtree(project_root)


def example_error_handling():
    """Example: Error handling scenarios."""
    print("\n=== Error Handling Examples ===")
    
    # 1. Non-existent project directory
    try:
        manager = AgentManager("/non/existent/directory")
        print(f"Manager created for non-existent directory: {len(manager.agents)} agents")
    except Exception as e:
        print(f"Error with non-existent directory: {e}")
    
    # 2. Invalid agent file
    temp_dir = Path(tempfile.mkdtemp())
    agents_dir = temp_dir / ".autocoderagents"
    agents_dir.mkdir()
    
    invalid_agent = """---
name: 
description: Agent with empty name
---
Invalid agent content.
"""
    
    try:
        (agents_dir / "invalid.md").write_text(invalid_agent)
        manager = AgentManager(str(temp_dir))
        print(f"Agents loaded despite invalid file: {len(manager.agents)}")
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run all examples."""
    print("AutoCoder Agents Module - Usage Examples")
    print("=" * 50)
    
    example_basic_usage()
    example_agent_parser()
    example_validation_errors()
    example_priority_system()
    example_render_sub_agents()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main() 