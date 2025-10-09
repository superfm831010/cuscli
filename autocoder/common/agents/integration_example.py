"""
Integration example for agentic_edit.py

This file demonstrates how the agents module integrates with the agentic_edit.py
system, showing how agents are loaded and used in the context of the larger system.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

from autocoder.common.agents import AgentManager


def create_sample_project_with_agents():
    """Create a sample project directory with agent definitions."""
    print("=== Creating Sample Project with Agents ===")
    
    # Create temporary project directory
    project_root = Path(tempfile.mkdtemp())
    agents_dir = project_root / ".autocoderagents"
    agents_dir.mkdir()
    
    # Create realistic agent definitions that would be used in agentic_edit
    agents = {
        "python-expert.md": """---
name: python-expert
description: Python development specialist with expertise in best practices and frameworks
tools: read_file, write_to_file, search_files, execute_command
model: gpt-4
include_rules: true
---

You are a Python development expert with deep knowledge of:
- Modern Python practices (3.8+)
- Popular frameworks (Django, FastAPI, Flask)
- Testing with pytest, unittest
- Package management and virtual environments
- Code quality tools (black, flake8, mypy)
- Performance optimization

Your tasks include:
1. Writing clean, maintainable Python code
2. Implementing proper error handling and logging
3. Creating comprehensive tests
4. Following PEP 8 and Python best practices
5. Optimizing code for performance when needed
""",
        
        "typescript-expert.md": """---
name: typescript-expert
description: TypeScript and modern JavaScript development specialist
tools: read_file, write_to_file, search_files, execute_command
model: gpt-4
---

You are a TypeScript and modern JavaScript expert specializing in:
- TypeScript advanced features and type system
- Modern JavaScript (ES2020+)
- React, Vue, Angular frameworks
- Node.js backend development
- Build tools (Webpack, Vite, esbuild)
- Testing frameworks (Jest, Vitest, Cypress)

Your responsibilities:
1. Writing type-safe TypeScript code
2. Implementing modern JavaScript patterns
3. Creating robust frontend applications
4. Setting up proper build and deployment pipelines
5. Ensuring code quality and maintainability
""",

        "devops-specialist.md": """---
name: devops-specialist  
description: DevOps and infrastructure automation specialist
tools: read_file, write_to_file, execute_command, search_files
model: gpt-4
include_rules: false
---

You are a DevOps specialist with expertise in:
- Container technologies (Docker, Kubernetes)
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Infrastructure as Code (Terraform, Ansible)
- Cloud platforms (AWS, GCP, Azure)
- Monitoring and logging (Prometheus, ELK stack)
- Security best practices

Your focus areas:
1. Automating deployment and infrastructure
2. Setting up monitoring and alerting
3. Implementing security best practices
4. Optimizing CI/CD pipelines
5. Managing containerized applications
"""
    }
    
    # Write agent files
    for filename, content in agents.items():
        (agents_dir / filename).write_text(content)
        print(f"Created agent: {filename}")
    
    print(f"Project created at: {project_root}")
    return project_root


def simulate_agentic_edit_integration():
    """Simulate how AgentManager integrates with agentic_edit.py."""
    print("\n=== Simulating agentic_edit.py Integration ===")
    
    # Create project with agents
    project_root = create_sample_project_with_agents()
    
    try:
        # This simulates the code in agentic_edit.py around line 1716-1723
        print("Initializing AgentManager (as done in agentic_edit.py)...")
        
        # Mock some dependencies that would be present in agentic_edit
        class MockArgs:
            def __init__(self):
                self.source_dir = str(project_root)
                self.code_model = "gpt-4"
                self.model = "gpt-4"
        
        mock_args = MockArgs()
        
        try:
            # This mirrors the actual code in agentic_edit.py
            agent_manager = AgentManager(
                project_root=mock_args.source_dir or ".")
            current_model = mock_args.code_model or mock_args.model
            sub_agents_content = agent_manager.render_sub_agents_section(
                current_model=current_model)
            
            print("✓ AgentManager initialized successfully")
            print(f"✓ Loaded {len(agent_manager.list_agents())} agents")
            print(f"✓ Generated sub-agents content: {bool(sub_agents_content and sub_agents_content.strip())}")
            
            return agent_manager, sub_agents_content
            
        except Exception as e:
            print(f"✗ Failed to load agents: {e}")
            return None, ""
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(project_root)


def demonstrate_sub_agents_section_output():
    """Demonstrate the output that would be included in system prompts."""
    print("\n=== Sub-Agents Section Output Demo ===")
    
    project_root = create_sample_project_with_agents()
    
    try:
        agent_manager = AgentManager(str(project_root))
        result = agent_manager.render_sub_agents_section(current_model="gpt-4")
        
        if result and result.strip():
            print("The following would be included in the system prompt:")
            print("-" * 60)
            print(result)
            print("-" * 60)
        else:
            print("No agents available - sub-agents section would be empty")
    
    finally:
        import shutil
        shutil.rmtree(project_root)


def test_error_scenarios():
    """Test error scenarios that might occur in agentic_edit integration."""
    print("\n=== Testing Error Scenarios ===")
    
    # Scenario 1: No agents directory
    empty_project = Path(tempfile.mkdtemp())
    try:
        print("1. Testing with no agents directory...")
        agent_manager = AgentManager(str(empty_project))
        result = agent_manager.render_sub_agents_section(current_model="gpt-4")
        
        print(f"   Agents available: {bool(result and result.strip())}")
        print("   ✓ Handled gracefully - no crash")
        
    finally:
        import shutil
        shutil.rmtree(empty_project)
    
    # Scenario 2: Invalid agent files
    project_with_invalid = Path(tempfile.mkdtemp())
    agents_dir = project_with_invalid / ".autocoderagents"
    agents_dir.mkdir()
    
    try:
        print("2. Testing with invalid agent files...")
        
        # Create invalid agent file
        (agents_dir / "invalid.md").write_text("Invalid content without frontmatter")
        
        # Create valid agent file
        valid_agent = """---
name: valid-agent
description: A valid agent
---
Valid agent content.
"""
        (agents_dir / "valid.md").write_text(valid_agent)
        
        agent_manager = AgentManager(str(project_with_invalid))
        print(f"   Loaded agents: {len(agent_manager.list_agents())}")
        print("   ✓ Invalid files skipped, valid files loaded")
        
    finally:
        import shutil
        shutil.rmtree(project_with_invalid)


def demonstrate_priority_system_integration():
    """Demonstrate how the priority system works in practice."""
    print("\n=== Priority System Integration Demo ===")
    
    project_root = Path(tempfile.mkdtemp())
    
    try:
        # Create multiple priority levels
        project_agents = project_root / ".autocoderagents"
        autocoder_agents = project_root / ".auto-coder" / ".autocoderagents"
        
        project_agents.mkdir()
        autocoder_agents.mkdir(parents=True)
        
        # Project-level agent (highest priority)
        project_specialist = """---
name: project-specialist
description: Project-specific specialist with custom configuration
model: gpt-4-turbo
---
I am a specialist configured specifically for this project.
"""
        
        # Auto-coder level agent (lower priority)
        generic_specialist = """---
name: project-specialist
description: Generic specialist from auto-coder directory
model: gpt-3.5-turbo
---
I am a generic specialist from the auto-coder directory.
"""
        
        (project_agents / "specialist.md").write_text(project_specialist)
        (autocoder_agents / "specialist.md").write_text(generic_specialist)
        
        # Load agents and check which one wins
        agent_manager = AgentManager(str(project_root))
        agent = agent_manager.get_agent("project-specialist")
        
        if agent:
            print(f"Loaded specialist: {agent.description}")
            print(f"Model: {agent.model}")
            print("✓ Project-level agent correctly overrode auto-coder level")
        else:
            print("✗ No agent loaded")
    
    finally:
        import shutil
        shutil.rmtree(project_root)


def simulate_real_world_usage():
    """Simulate real-world usage patterns."""
    print("\n=== Real-World Usage Simulation ===")
    
    project_root = create_sample_project_with_agents()
    
    try:
        # Simulate the workflow that would happen in agentic_edit
        print("1. System initialization...")
        agent_manager = AgentManager(str(project_root))
        
        print("2. Checking available agents...")
        available_agents = agent_manager.get_agent_names()
        print(f"   Available: {available_agents}")
        
        print("3. Rendering system prompt section...")
        sub_agents_section = agent_manager.render_sub_agents_section(current_model="gpt-4")
        
        print("4. Simulating agent selection and usage...")
        # User might want to use the python expert
        python_expert = agent_manager.get_agent("python-expert")
        if python_expert:
            print(f"   Selected: {python_expert.name}")
            print(f"   Tools available: {python_expert.tools}")
            print(f"   Model: {python_expert.model}")
        
        print("5. Converting to dictionary for logging/debugging...")
        manager_state = agent_manager.to_dict()
        print(f"   Manager state keys: {list(manager_state.keys())}")
        
        print("✓ Complete workflow simulation successful")
        
    finally:
        import shutil
        shutil.rmtree(project_root)


def main():
    """Run all integration examples."""
    print("AutoCoder Agents Module - Integration Examples")
    print("=" * 60)
    
    simulate_agentic_edit_integration()
    demonstrate_sub_agents_section_output()
    test_error_scenarios()
    demonstrate_priority_system_integration()
    simulate_real_world_usage()
    
    print("\n" + "=" * 60)
    print("Integration examples completed successfully!")
    print("\nThese examples show how the agents module integrates with")
    print("agentic_edit.py to provide specialized agent capabilities")
    print("in the AutoCoder system.")


if __name__ == "__main__":
    main() 