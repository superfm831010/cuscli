
"""
Agent Parser Module

This module provides functionality to parse agent definitions from markdown files.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class Agent:
    """Represents an agent definition."""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    model: Optional[str] = None
    content: str = ""
    file_path: Optional[Path] = None
    include_rules: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'tools': self.tools,
            'model': self.model,
            'content': self.content,
            'file_path': str(self.file_path) if self.file_path else None,
            'include_rules': self.include_rules
        }


class AgentParser:
    """Parser for agent definition files."""
    
    @staticmethod
    def parse_agent_file(file_path: Path) -> Agent:
        """
        Parse an agent definition from a markdown file.
        
        Args:
            file_path: Path to the .md file containing agent definition
            
        Returns:
            Agent: Parsed agent object
            
        Raises:
            ValueError: If the file format is invalid
        """
        if not file_path.exists():
            raise ValueError(f"Agent file not found: {file_path}")
            
        content = file_path.read_text(encoding='utf-8')
        return AgentParser.parse_agent_content(content, file_path)
    
    @staticmethod
    def parse_agent_content(content: str, file_path: Optional[Path] = None) -> Agent:
        """
        Parse agent definition from content string.
        
        Args:
            content: The content of the agent definition
            file_path: Optional path to the source file
            
        Returns:
            Agent: Parsed agent object
            
        Raises:
            ValueError: If the content format is invalid
        """
        # Split content into frontmatter and body
        parts = content.split('---', 2)
        
        if len(parts) < 3:
            raise ValueError("Invalid agent file format. Expected YAML frontmatter between --- markers.")
        
        # Parse YAML frontmatter
        frontmatter_str = parts[1].strip()
        
        # Handle special case: tools: * (fix YAML alias issue)
        # Replace 'tools: *' with 'tools: "*"' to make it a string literal
        frontmatter_str = frontmatter_str.replace('tools: *', 'tools: "*"')
        
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a valid YAML dictionary")
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML frontmatter: {e}")
        
        # Extract required fields
        name = frontmatter.get('name')
        if not name:
            raise ValueError("Agent definition must include 'name' field")
            
        description = frontmatter.get('description')
        if not description:
            raise ValueError("Agent definition must include 'description' field")
        
        # Extract optional fields
        tools_str = frontmatter.get('tools', '')
        tools = AgentParser._parse_tools(tools_str)
        
        model = frontmatter.get('model')
        include_rules = frontmatter.get('include_rules', False)
        
        # The body content (system prompt)
        body_content = parts[2].strip()
        
        return Agent(
            name=name,
            description=description,
            tools=tools,
            model=model,
            content=body_content,
            file_path=file_path,
            include_rules=include_rules
        )
    
    @staticmethod
    def _parse_tools(tools_str: str) -> List[str]:
        """
        Parse tools string into a list of tool names.
        
        Args:
            tools_str: Comma-separated string of tool names, or "*" for all tools
            
        Returns:
            List[str]: List of tool names
        """
        if not tools_str:
            return []
        
        # Handle special case: "*" means all tools
        if tools_str.strip() == "*":
            return ["*"]  # Keep as "*" to indicate all tools
            
        # Split by comma and clean up each tool name
        tools = [tool.strip() for tool in tools_str.split(',')]
        # Remove empty strings
        tools = [tool for tool in tools if tool]
        
        return tools
    
    @staticmethod
    def validate_agent(agent: Agent) -> List[str]:
        """
        Validate an agent definition.
        
        Args:
            agent: The agent to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        if not agent.name:
            errors.append("Agent name is required")
            
        if not agent.description:
            errors.append("Agent description is required")
            
        if not agent.content:
            errors.append("Agent content (system prompt) is required")
            
        # Validate tool names (basic validation)
        # Tool names should match those defined in agentic_edit_types.py TOOL_MODEL_MAP
        valid_tools = {
            'execute_command', 'read_file', 'write_to_file', 'replace_in_file', 
            'search_files', 'list_files', 
            'ask_followup_question', 'attempt_completion',
            'use_mcp_tool', 'use_rag_tool', 'run_named_subagents',
            'todo_read', 'todo_write', 'ac_mod_read', 'ac_mod_write', 'ac_mod_list',
            'count_tokens',             
            '*'  # Special case for all tools
        }
        for tool in agent.tools:
            if tool not in valid_tools:
                errors.append(f"Unknown tool: {tool}. Valid tools are: {', '.join(sorted(valid_tools - {'*'}))}, or '*' for all tools")
        
        return errors

