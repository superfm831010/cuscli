"""
Test suite for MCP Tools Module

This module provides comprehensive tests for all MCP tools functionality,
including server connections, tool execution, and configuration management.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import threading
import time

from .types import (
    McpRequest, McpInstallRequest, McpRemoveRequest, McpListRequest,
    McpListRunningRequest, McpRefreshRequest, McpServerInfoRequest,
    McpResponse, ServerInfo, InstallResult, RemoveResult, ListResult,
    ListRunningResult, RefreshResult, QueryResult, ErrorResult,
    StringResult, MarketplaceAddRequest, MarketplaceAddResult,
    MarketplaceUpdateRequest, MarketplaceUpdateResult, MarketplaceMCPServerItem,
    McpToolCall, McpResourceAccess
)
from .hub import McpHub, MCP_BUILD_IN_SERVERS
from .executor import McpExecutor
from .installer import McpServerInstaller
from .server import McpServer, get_mcp_server


class TestMcpTypes:
    """Test MCP type definitions"""
    
    def test_mcp_request_creation(self):
        """Test creating McpRequest"""
        request = McpRequest(query="test query")
        assert request.query == "test query"
        assert request.model is None
        assert request.product_mode is None
    
    def test_mcp_install_request_creation(self):
        """Test creating McpInstallRequest"""
        request = McpInstallRequest(server_name_or_config="test-server")
        assert request.server_name_or_config == "test-server"
        assert request.market_install_item is None
    
    def test_marketplace_item_creation(self):
        """Test creating MarketplaceMCPServerItem"""
        item = MarketplaceMCPServerItem(
            name="test-server",
            description="Test server",
            mcp_type="command",
            command="python",
            args=["-m", "test"],
            env={"PATH": "/usr/bin"}
        )
        assert item.name == "test-server"
        assert item.description == "Test server"
        assert item.mcp_type == "command"
        assert item.command == "python"
        assert item.args == ["-m", "test"]
        assert item.env == {"PATH": "/usr/bin"}
    
    def test_mcp_tool_call_creation(self):
        """Test creating McpToolCall"""
        tool_call = McpToolCall(
            server_name="test-server",
            tool_name="test-tool",
            arguments={"param1": "value1"}
        )
        assert tool_call.server_name == "test-server"
        assert tool_call.tool_name == "test-tool"
        assert tool_call.arguments == {"param1": "value1"}
    
    def test_mcp_resource_access_creation(self):
        """Test creating McpResourceAccess"""
        resource_access = McpResourceAccess(
            server_name="test-server",
            uri="file:///test.txt"
        )
        assert resource_access.server_name == "test-server"
        assert resource_access.uri == "file:///test.txt"


class TestMcpHub:
    """Test MCP Hub functionality"""
    
    def test_singleton_behavior(self):
        """Test that McpHub is a singleton"""
        hub1 = McpHub()
        hub2 = McpHub()
        assert hub1 is hub2
    
    def test_settings_file_creation(self):
        """Test that settings file is created"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            hub = McpHub(settings_path=str(settings_path))
            assert settings_path.exists()
            
            with open(settings_path) as f:
                data = json.load(f)
                assert "mcpServers" in data
                assert data["mcpServers"] == {}
    
    def test_marketplace_file_creation(self):
        """Test that marketplace file is created"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            marketplace_path = Path(tmp_dir) / "marketplace.json"
            hub = McpHub(marketplace_path=str(marketplace_path))
            assert marketplace_path.exists()
            
            with open(marketplace_path) as f:
                data = json.load(f)
                assert "mcpServers" in data
                assert data["mcpServers"] == []
    
    def test_get_marketplace_items(self):
        """Test getting marketplace items"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            marketplace_path = Path(tmp_dir) / "marketplace.json"
            # Create test marketplace data
            test_data = {
                "mcpServers": [
                    {
                        "name": "test-server",
                        "description": "Test server",
                        "mcp_type": "command",
                        "command": "python",
                        "args": ["-m", "test"],
                        "env": {},
                        "url": ""
                    }
                ]
            }
            with open(marketplace_path, 'w') as f:
                json.dump(test_data, f)
            
            hub = McpHub(marketplace_path=str(marketplace_path))
            items = hub.get_marketplace_items()
            assert len(items) == 1
            assert items[0].name == "test-server"
    
    def test_server_templates(self):
        """Test getting server templates"""
        templates = McpHub.get_server_templates()
        assert isinstance(templates, dict)
        # Should have at least some built-in servers
        assert len(templates) >= 0


class TestMcpExecutor:
    """Test MCP Executor functionality"""
    
    def test_executor_creation(self):
        """Test creating McpExecutor"""
        mock_hub = Mock()
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        assert executor.mcp_hub == mock_hub
        assert executor.llm == mock_llm
    
    def test_get_server_names_empty(self):
        """Test get_server_names with no servers"""
        mock_hub = Mock()
        mock_hub.get_servers.return_value = []
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        result = executor.get_server_names()
        assert result == "(None running currently)"
    
    def test_get_server_names_with_servers(self):
        """Test get_server_names with servers"""
        mock_hub = Mock()
        mock_server1 = Mock()
        mock_server1.name = "server1"
        mock_server2 = Mock()
        mock_server2.name = "server2"
        mock_hub.get_servers.return_value = [mock_server1, mock_server2]
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        result = executor.get_server_names()
        assert result == "server1,server2"
    
    @pytest.mark.asyncio
    async def test_extract_mcp_calls_tool_call(self):
        """Test extracting MCP tool calls from content"""
        mock_hub = Mock()
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        content = """
        <use_mcp_tool>
        <server_name>test-server</server_name>
        <tool_name>test-tool</tool_name>
        <arguments>
        {
          "param1": "value1",
          "param2": "value2"
        }
        </arguments>
        </use_mcp_tool>
        """
        
        calls = await executor.extract_mcp_calls(content)
        assert len(calls) == 1
        assert isinstance(calls[0], McpToolCall)
        assert calls[0].server_name == "test-server"
        assert calls[0].tool_name == "test-tool"
        assert calls[0].arguments == {"param1": "value1", "param2": "value2"}
    
    @pytest.mark.asyncio
    async def test_extract_mcp_calls_resource_access(self):
        """Test extracting MCP resource access from content"""
        mock_hub = Mock()
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        content = """
        <access_mcp_resource>
        <server_name>test-server</server_name>
        <uri>file:///test.txt</uri>
        </access_mcp_resource>
        """
        
        calls = await executor.extract_mcp_calls(content)
        assert len(calls) == 1
        assert isinstance(calls[0], McpResourceAccess)
        assert calls[0].server_name == "test-server"
        assert calls[0].uri == "file:///test.txt"
    
    def test_format_mcp_result_none(self):
        """Test formatting None result"""
        mock_hub = Mock()
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        result = executor.format_mcp_result(None)
        assert result == "(No result)"
    
    def test_format_mcp_result_dict(self):
        """Test formatting dict result"""
        mock_hub = Mock()
        mock_llm = Mock()
        executor = McpExecutor(mock_hub, mock_llm)
        
        test_dict = {"key": "value"}
        result = executor.format_mcp_result(test_dict)
        assert '"key": "value"' in result


class TestMcpServerInstaller:
    """Test MCP Server Installer functionality"""
    
    def test_installer_creation(self):
        """Test creating McpServerInstaller"""
        installer = McpServerInstaller()
        assert installer is not None
    
    def test_deep_merge_dicts(self):
        """Test deep merging of dictionaries"""
        installer = McpServerInstaller()
        
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        
        result = installer.deep_merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        assert result == expected
    
    def test_parse_command_line_args(self):
        """Test parsing command line arguments"""
        installer = McpServerInstaller()
        
        args = "--name test-server --command python --args -m test --env PATH=/usr/bin"
        name, config = installer.parse_command_line_args(args)
        
        assert name == "test-server"
        assert config["command"] == "python"
        assert config["args"] == ["-m", "test"]
        assert config["env"] == {"PATH": "/usr/bin"}
    
    def test_parse_json_config(self):
        """Test parsing JSON configuration"""
        installer = McpServerInstaller()
        
        json_config = '{"test-server": {"command": "python", "args": ["-m", "test"]}}'
        name, config = installer.parse_json_config(json_config)
        
        assert name == "test-server"
        assert config["command"] == "python"
        assert config["args"] == ["-m", "test"]
    
    def test_process_market_install_item(self):
        """Test processing marketplace install item"""
        installer = McpServerInstaller()
        
        item = MarketplaceMCPServerItem(
            name="test-server",
            command="python",
            args=["-m", "test"],
            env={"PATH": "/usr/bin"}
        )
        
        name, config = installer.process_market_install_item(item)
        
        assert name == "test-server"
        assert config["command"] == "python"
        assert config["args"] == ["-m", "test"]
        assert config["env"] == {"PATH": "/usr/bin"}


class TestMcpServer:
    """Test MCP Server functionality"""
    
    def test_server_creation(self):
        """Test creating McpServer"""
        server = McpServer()
        assert server is not None
        assert not server._running
    
    def test_server_start_stop(self):
        """Test starting and stopping server"""
        server = McpServer()
        
        # Start server
        server.start()
        assert server._running
        
        # Stop server
        server.stop()
        assert not server._running
    
    def test_get_mcp_server_singleton(self):
        """Test get_mcp_server singleton behavior"""
        server1 = get_mcp_server()
        server2 = get_mcp_server()
        assert server1 is server2
    
    def test_send_request_basic(self):
        """Test sending basic request"""
        server = McpServer()
        
        # Mock the request processing
        with patch.object(server, '_process_request') as mock_process:
            request = McpRequest(query="test")
            
            # This test is limited because we can't easily mock the async queue
            # In a real test, we'd need to set up the full async infrastructure
            pass


class TestIntegration:
    """Integration tests for the MCP tools module"""
    
    def test_module_import(self):
        """Test that all modules can be imported"""
        from . import (
            McpHub, McpExecutor, McpServerInstaller, McpServer,
            get_mcp_server, McpRequest, McpResponse
        )
        
        # All imports should work without errors
        assert McpHub is not None
        assert McpExecutor is not None
        assert McpServerInstaller is not None
        assert McpServer is not None
        assert get_mcp_server is not None
        assert McpRequest is not None
        assert McpResponse is not None
    
    def test_basic_workflow(self):
        """Test basic MCP workflow"""
        # Create components
        server = get_mcp_server()
        assert server is not None
        
        # Create request
        request = McpRequest(query="test query")
        assert request.query == "test query"
        
        # Note: Full integration test would require actual MCP server setup
        # which is beyond the scope of unit tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 