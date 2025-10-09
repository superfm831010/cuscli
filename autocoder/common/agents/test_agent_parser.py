"""
Comprehensive test suite for the agents module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from autocoder.common.agents import AgentManager, AgentParser, Agent


# Test data for agent definitions
VALID_AGENT_CONTENT = """---
name: test-agent
description: A test agent for validation
tools: read_file, write_to_file, execute_command
model: gpt-4
---

You are a test agent designed to help with testing scenarios.
Your task is to assist users with their testing needs.
"""

MINIMAL_AGENT_CONTENT = """---
name: minimal-agent
description: Minimal agent with required fields only
---

You are a minimal agent with only the required fields.
"""

WILDCARD_TOOLS_AGENT_CONTENT = """---
name: wildcard-agent
description: Agent with wildcard tools
tools: *
model: gpt-4
---

You are an agent with access to all tools.
"""

INCLUDE_RULES_AGENT_CONTENT = """---
name: rules-agent
description: Agent with include_rules enabled
tools: read_file, write_to_file
model: gpt-4
include_rules: true
---

You are an agent that includes rules in processing.
"""

INVALID_AGENT_NO_FRONTMATTER = """
This is just content without frontmatter.
"""

INVALID_AGENT_NO_NAME = """---
description: Agent without name
---

Agent content here.
"""

INVALID_AGENT_YAML_ERROR = """---
name: invalid-yaml
description: Agent with invalid YAML
tools: [unclosed list
---

Agent content here.
"""


class TestAgent:
    """Test cases for the Agent dataclass."""
    
    def test_agent_creation(self):
        """Test creating an agent with all fields."""
        agent = Agent(
            name="test-agent",
            description="Test description",
            tools=["read_file", "write_to_file"],
            model="gpt-4",
            content="Test content",
            file_path=Path("/test/path.md"),
            include_rules=True
        )
        
        assert agent.name == "test-agent"
        assert agent.description == "Test description"
        assert agent.tools == ["read_file", "write_to_file"]
        assert agent.model == "gpt-4"
        assert agent.content == "Test content"
        assert agent.file_path == Path("/test/path.md")
        assert agent.include_rules == True
    
    def test_agent_defaults(self):
        """Test agent with default values."""
        agent = Agent(name="test", description="desc")
        
        assert agent.tools == []
        assert agent.model is None
        assert agent.content == ""
        assert agent.file_path is None
        assert agent.include_rules == False
    
    def test_agent_to_dict(self):
        """Test converting agent to dictionary."""
        agent = Agent(
            name="test-agent",
            description="Test description",
            tools=["read_file", "write_to_file"],
            model="gpt-4",
            content="Test content",
            file_path=Path("/test/path.md"),
            include_rules=True
        )
        
        expected = {
            'name': 'test-agent',
            'description': 'Test description',
            'tools': ['read_file', 'write_to_file'],
            'model': 'gpt-4',
            'content': 'Test content',
            'file_path': '/test/path.md',
            'include_rules': True
        }
        
        assert agent.to_dict() == expected
    
    def test_agent_to_dict_with_none_path(self):
        """Test converting agent to dictionary with None file_path."""
        agent = Agent(name="test", description="desc")
        result = agent.to_dict()
        
        assert result['file_path'] is None
        assert result['include_rules'] == False


class TestAgentParser:
    """Test cases for the AgentParser class."""
    
    def test_parse_valid_agent_content(self):
        """Test parsing valid agent content."""
        agent = AgentParser.parse_agent_content(VALID_AGENT_CONTENT)
        
        assert agent.name == "test-agent"
        assert agent.description == "A test agent for validation"
        assert agent.tools == ["read_file", "write_to_file", "execute_command"]
        assert agent.model == "gpt-4"
        assert "You are a test agent" in agent.content
        assert agent.file_path is None
    
    def test_parse_minimal_agent_content(self):
        """Test parsing agent with minimal required fields."""
        agent = AgentParser.parse_agent_content(MINIMAL_AGENT_CONTENT)
        
        assert agent.name == "minimal-agent"
        assert agent.description == "Minimal agent with required fields only"
        assert agent.tools == []
        assert agent.model is None
        assert agent.include_rules == False  # default value when not specified
        assert "You are a minimal agent" in agent.content
    
    def test_parse_wildcard_tools_agent_content(self):
        """Test parsing agent with wildcard tools."""
        agent = AgentParser.parse_agent_content(WILDCARD_TOOLS_AGENT_CONTENT)
        
        assert agent.name == "wildcard-agent"
        assert agent.description == "Agent with wildcard tools"
        assert agent.tools == ["*"]
        assert agent.model == "gpt-4"
        assert agent.include_rules == False  # default value
        assert "You are an agent with access to all tools" in agent.content
    
    def test_parse_include_rules_agent_content(self):
        """Test parsing agent with include_rules enabled."""
        agent = AgentParser.parse_agent_content(INCLUDE_RULES_AGENT_CONTENT)
        
        assert agent.name == "rules-agent"
        assert agent.description == "Agent with include_rules enabled"
        assert agent.tools == ["read_file", "write_to_file"]
        assert agent.model == "gpt-4"
        assert agent.include_rules == True
        assert "You are an agent that includes rules" in agent.content
    
    def test_parse_invalid_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        with pytest.raises(ValueError, match="Invalid agent file format"):
            AgentParser.parse_agent_content(INVALID_AGENT_NO_FRONTMATTER)
    
    def test_parse_invalid_no_name(self):
        """Test parsing agent without name field."""
        with pytest.raises(ValueError, match="Agent definition must include 'name' field"):
            AgentParser.parse_agent_content(INVALID_AGENT_NO_NAME)
    
    def test_parse_invalid_yaml(self):
        """Test parsing agent with invalid YAML."""
        with pytest.raises(ValueError, match="Failed to parse YAML frontmatter"):
            AgentParser.parse_agent_content(INVALID_AGENT_YAML_ERROR)
    
    def test_parse_tools_empty(self):
        """Test parsing empty tools string."""
        assert AgentParser._parse_tools("") == []
        assert AgentParser._parse_tools("   ") == []
    
    def test_parse_tools_single(self):
        """Test parsing single tool."""
        assert AgentParser._parse_tools("Read") == ["Read"]
        assert AgentParser._parse_tools("  Read  ") == ["Read"]
    
    def test_parse_tools_multiple(self):
        """Test parsing multiple tools."""
        assert AgentParser._parse_tools("Read, Write, Bash") == ["Read", "Write", "Bash"]
        assert AgentParser._parse_tools("Read,Write,Bash") == ["Read", "Write", "Bash"]
        assert AgentParser._parse_tools("  Read , Write , Bash  ") == ["Read", "Write", "Bash"]
    
    def test_parse_agent_file_not_found(self):
        """Test parsing non-existent file."""
        with pytest.raises(ValueError, match="Agent file not found"):
            AgentParser.parse_agent_file(Path("/non/existent/file.md"))
    
    def test_parse_agent_file_valid(self):
        """Test parsing valid agent file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(VALID_AGENT_CONTENT)
            temp_path = Path(f.name)
        
        try:
            agent = AgentParser.parse_agent_file(temp_path)
            assert agent.name == "test-agent"
            assert agent.file_path == temp_path
        finally:
            temp_path.unlink()
    
    def test_validate_agent_valid(self):
        """Test validating a valid agent."""
        agent = Agent(
            name="test-agent",
            description="Test description",
            tools=["read_file", "write_to_file"],
            content="Test content"
        )
        
        errors = AgentParser.validate_agent(agent)
        assert errors == []
    
    def test_validate_agent_missing_name(self):
        """Test validating agent without name."""
        agent = Agent(name="", description="desc", content="content")
        errors = AgentParser.validate_agent(agent)
        assert "Agent name is required" in errors
    
    def test_validate_agent_missing_description(self):
        """Test validating agent without description."""
        agent = Agent(name="test", description="", content="content")
        errors = AgentParser.validate_agent(agent)
        assert "Agent description is required" in errors
    
    def test_validate_agent_missing_content(self):
        """Test validating agent without content."""
        agent = Agent(name="test", description="desc", content="")
        errors = AgentParser.validate_agent(agent)
        assert "Agent content (system prompt) is required" in errors
    
    def test_validate_agent_invalid_tools(self):
        """Test validating agent with invalid tools."""
        agent = Agent(
            name="test",
            description="desc",
            content="content",
            tools=["read_file", "InvalidTool", "write_to_file"]
        )
        errors = AgentParser.validate_agent(agent)
        assert any("Unknown tool: InvalidTool" in error for error in errors)
    
    def test_validate_agent_wildcard_tools(self):
        """Test validating agent with wildcard tools."""
        agent = Agent(
            name="test",
            description="desc",
            content="content",
            tools=["*"]
        )
        errors = AgentParser.validate_agent(agent)
        assert errors == []  # "*" should be valid
    
    def test_validate_agent_multiple_errors(self):
        """Test validating agent with multiple errors."""
        agent = Agent(
            name="",
            description="",
            content="",
            tools=["InvalidTool"]
        )
        errors = AgentParser.validate_agent(agent)
        assert len(errors) == 4  # name, description, content, tool


class TestAgentManager:
    """Test cases for the AgentManager class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def agents_dir(self, temp_project):
        """Create agents directory with test files."""
        agents_dir = temp_project / ".autocoderagents"
        agents_dir.mkdir()
        
        # Create test agent files
        (agents_dir / "test-agent.md").write_text(VALID_AGENT_CONTENT)
        (agents_dir / "minimal-agent.md").write_text(MINIMAL_AGENT_CONTENT)
        
        return agents_dir
    
    def test_agent_manager_initialization(self, temp_project):
        """Test AgentManager initialization."""
        manager = AgentManager(str(temp_project))
        assert manager.project_root == temp_project
        assert isinstance(manager.agents, dict)
    
    def test_load_agents_from_directory(self, temp_project, agents_dir):
        """Test loading agents from directory."""
        with patch.object(AgentManager, '_load_agents') as mock_load:
            manager = AgentManager(str(temp_project))
            mock_load.reset_mock()  # Reset the mock after __init__
            
            # Manually test the loading method
            manager._load_agents_from_directory(agents_dir)
            
            assert len(manager.agents) == 2
            assert "test-agent" in manager.agents
            assert "minimal-agent" in manager.agents
    
    def test_get_agent_existing(self, temp_project, agents_dir):
        """Test getting an existing agent."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        agent = manager.get_agent("test-agent")
        assert agent is not None
        assert agent.name == "test-agent"
    
    def test_get_agent_non_existing(self, temp_project):
        """Test getting a non-existing agent."""
        manager = AgentManager(str(temp_project))
        agent = manager.get_agent("non-existing")
        assert agent is None
    
    def test_list_agents(self, temp_project, agents_dir):
        """Test listing all agents."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        agents = manager.list_agents()
        assert len(agents) == 2
        agent_names = [agent.name for agent in agents]
        assert "test-agent" in agent_names
        assert "minimal-agent" in agent_names
    
    def test_get_agent_names(self, temp_project, agents_dir):
        """Test getting agent names."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        names = manager.get_agent_names()
        assert len(names) == 2
        assert "test-agent" in names
        assert "minimal-agent" in names
    
    def test_reload_agents(self, temp_project, agents_dir):
        """Test reloading agents."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        # Add a new agent file
        new_agent_content = """---
name: new-agent
description: Newly added agent
---
New agent content.
"""
        (agents_dir / "new-agent.md").write_text(new_agent_content)
        
        # Mock the _load_agents method to use our test directory
        with patch.object(manager, '_load_agents') as mock_load:
            mock_load.side_effect = lambda: manager._load_agents_from_directory(agents_dir)
            manager.reload_agents()
            mock_load.assert_called_once()
    
    def test_render_sub_agents_section_no_agents(self, temp_project):
        """Test rendering sub agents section when no agents are loaded."""
        manager = AgentManager(str(temp_project))
        result = manager.render_sub_agents_section()
        # The method returns a rendered template string, so we check if it's empty or minimal
        assert isinstance(result, str)
        # For no agents, the template should render to empty or minimal content
        assert len(result.strip()) == 0 or "Available Sub Agents" not in result
    
    def test_render_sub_agents_section_with_agents(self, temp_project, agents_dir):
        """Test rendering sub agents section with loaded agents."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        result = manager.render_sub_agents_section(current_model="gpt-4")
        # The method returns a rendered template string
        assert isinstance(result, str)
        # Check that the rendered template contains expected content
        assert "Available Named Sub Agents" in result
        assert "test-agent" in result
        assert "minimal-agent" in result
        assert "run_named_subagents" in result
    
    def test_render_sub_agents_section_no_model(self, temp_project, agents_dir):
        """Test rendering sub agents section without model raises error."""
        manager = AgentManager(str(temp_project))
        # Create agent without model
        agent_content = """---
name: no-model-agent
description: Agent without model
---
Agent content.
"""
        (agents_dir / "no-model.md").write_text(agent_content)
        manager._load_agents_from_directory(agents_dir)
        
        with pytest.raises(ValueError, match="has no model specified"):
            manager.render_sub_agents_section()
    
    def test_to_dict(self, temp_project, agents_dir):
        """Test converting manager to dictionary."""
        manager = AgentManager(str(temp_project))
        manager._load_agents_from_directory(agents_dir)
        
        result = manager.to_dict()
        assert "project_root" in result
        assert "search_paths" in result
        assert "agents" in result
        assert len(result["agents"]) == 2
    
    def test_agent_priority_override(self, temp_project):
        """Test that higher priority agents override lower priority ones."""
        # Create agents in different priority directories
        high_priority_dir = temp_project / ".autocoderagents"
        low_priority_dir = temp_project / ".auto-coder" / ".autocoderagents"
        
        high_priority_dir.mkdir()
        low_priority_dir.mkdir(parents=True)
        
        # Same agent name in both directories
        agent_low = """---
name: conflict-agent
description: Low priority agent
---
Low priority content.
"""
        agent_high = """---
name: conflict-agent
description: High priority agent
---
High priority content.
"""
        
        (low_priority_dir / "conflict.md").write_text(agent_low)
        (high_priority_dir / "conflict.md").write_text(agent_high)
        
        manager = AgentManager(str(temp_project))
        
        # Test fallback loading to simulate the behavior
        manager._load_agents_fallback()
        
        # High priority should win
        agent = manager.get_agent("conflict-agent")
        assert agent is not None
        assert agent.description == "High priority agent"


@pytest.mark.integration
class TestAgentManagerIntegration:
    """Integration tests for AgentManager with priority directory finder."""
    
    @pytest.fixture
    def complex_project(self):
        """Create a complex project with multiple agent directories."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create different priority directories
        project_agents = project_root / ".autocoderagents"
        autocoder_agents = project_root / ".auto-coder" / ".autocoderagents"
        
        project_agents.mkdir()
        autocoder_agents.mkdir(parents=True)
        
        # Add agents to each directory
        project_agent = """---
name: project-agent
description: Project level agent
---
Project level agent content.
"""
        autocoder_agent = """---
name: autocoder-agent
description: Auto-coder level agent
---
Auto-coder level agent content.
"""
        
        (project_agents / "project.md").write_text(project_agent)
        (autocoder_agents / "autocoder.md").write_text(autocoder_agent)
        
        yield project_root
        shutil.rmtree(temp_dir)
    
    @patch('autocoder.common.agents.agent_manager.PriorityDirectoryFinder')
    def test_priority_finder_integration(self, mock_finder_class, complex_project):
        """Test integration with priority directory finder."""
        # Mock the finder to return successful result
        mock_finder = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.primary_directory = str(complex_project / ".autocoderagents")
        mock_finder.find_directories.return_value = mock_result
        mock_finder_class.return_value = mock_finder
        
        manager = AgentManager(str(complex_project))
        
        # Verify finder was called with correct config
        assert mock_finder_class.called
        assert mock_finder.find_directories.called
        
        # Should load from the primary directory
        assert "project-agent" in manager.agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 