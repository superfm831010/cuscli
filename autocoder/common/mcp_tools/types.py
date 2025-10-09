"""
MCP Tools Types Module

This module contains all the type definitions used in the MCP tools system,
including request/response models, server configurations, and result types.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class MarketplaceMCPServerItem(BaseModel):
    """Represents an MCP server item"""

    name: str
    description: Optional[str] = ""
    mcp_type: str = "command"  # command/sse
    command: str = ""  # npm/uvx/python/node/...
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: str = ""  # sse url
    

class McpRequest(BaseModel):
    """Base request for MCP operations"""
    query: str
    model: Optional[str] = None
    product_mode: Optional[str] = None


class McpInstallRequest(BaseModel):
    """Request to install an MCP server"""
    server_name_or_config: Optional[str] = None
    market_install_item: Optional[MarketplaceMCPServerItem] = None


class McpRemoveRequest(BaseModel):
    """Request to remove an MCP server"""
    server_name: str


class McpListRequest(BaseModel):
    """Request to list all builtin MCP servers"""
    path: str = "/list"


class McpListRunningRequest(BaseModel):
    """Request to list all running MCP servers"""
    path: str = "/list/running"


class McpRefreshRequest(BaseModel):
    """Request to refresh MCP server connections"""
    name: Optional[str] = None


class McpServerInfoRequest(BaseModel):
    """Request to get MCP server info"""
    model: Optional[str] = None
    product_mode: Optional[str] = None


class MarketplaceAddRequest(BaseModel):
    """Request to add a new marketplace item"""
    name: str
    description: Optional[str] = ""
    mcp_type: str = "command"  # command/sse
    command: Optional[str] = ""  # npm/uvx/python/node/...
    args: Optional[List[str]] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    url: Optional[str] = ""  # sse url


class MarketplaceUpdateRequest(BaseModel):
    """Request to update an existing marketplace item"""
    name: str
    description: Optional[str] = ""
    mcp_type: str = "command"  # command/sse
    command: Optional[str] = ""  # npm/uvx/python/node/...
    args: Optional[List[str]] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    url: Optional[str] = ""  # sse url


# Result types
class ServerConfig(BaseModel):
    """Server configuration"""
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class InstallResult(BaseModel):
    """Result of server installation"""
    success: bool
    server_name: Optional[str] = None
    config: Optional[ServerConfig] = None
    error: Optional[str] = None


class RemoveResult(BaseModel):
    """Result of server removal"""
    success: bool
    server_name: Optional[str] = None
    error: Optional[str] = None


class ExternalServerInfo(BaseModel):
    """External server information"""
    name: str
    description: str


class ListResult(BaseModel):
    """Result of server listing"""
    builtin_servers: List[MarketplaceMCPServerItem] = Field(default_factory=list)
    external_servers: List[MarketplaceMCPServerItem] = Field(default_factory=list)
    marketplace_items: List[MarketplaceMCPServerItem] = Field(default_factory=list)
    error: Optional[str] = None


class ServerInfo(BaseModel):
    """Server information"""
    name: str


class ListRunningResult(BaseModel):
    """Result of running servers listing"""
    servers: List[ServerInfo] = Field(default_factory=list)
    error: Optional[str] = None


class RefreshResult(BaseModel):
    """Result of server refresh"""
    success: bool
    name: Optional[str] = None
    error: Optional[str] = None


class QueryResult(BaseModel):
    """Result of MCP query"""
    success: bool
    results: Optional[List[Any]] = None
    error: Optional[str] = None


class ErrorResult(BaseModel):
    """Error result"""
    success: bool = False
    error: str


class StringResult(BaseModel):
    """String result"""
    success: bool = True
    result: str


class MarketplaceAddResult(BaseModel):
    """Result for marketplace add operation"""
    success: bool
    name: str
    error: Optional[str] = None


class MarketplaceUpdateResult(BaseModel):
    """Result for marketplace update operation"""
    success: bool
    name: str
    error: Optional[str] = None


class McpExternalServer(BaseModel):
    """Represents an external MCP server configuration"""
    name: str
    description: str
    vendor: str
    sourceUrl: str
    homepage: str
    license: str
    runtime: str


class McpResponse(BaseModel):
    """MCP response containing result and optional error"""
    result: str
    error: Optional[str] = None
    raw_result: Optional[Union[
        InstallResult, MarketplaceAddResult, MarketplaceUpdateResult, 
        RemoveResult, ListResult, ListRunningResult, RefreshResult, 
        QueryResult, ErrorResult, StringResult
    ]] = None


# Tool and resource access types
class McpTool(BaseModel):
    """Represents an MCP tool configuration"""
    name: str
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict)


class McpResource(BaseModel):
    """Represents an MCP resource configuration"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class McpResourceTemplate(BaseModel):
    """Represents an MCP resource template"""
    uri_template: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class McpServer(BaseModel):
    """Represents an MCP server configuration and status"""
    name: str
    config: str  # JSON string of server config
    status: str = "disconnected"  # connected, disconnected, connecting
    error: Optional[str] = None
    tools: List[McpTool] = Field(default_factory=list)
    resources: List[McpResource] = Field(default_factory=list)
    resource_templates: List[McpResourceTemplate] = Field(default_factory=list)


class McpToolCall(BaseModel):
    """Represents an MCP tool call"""
    server_name: str = Field(..., description="The name of the MCP server")
    tool_name: str = Field(..., description="The name of the tool to call")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="The arguments to pass to the tool"
    )


class McpResourceAccess(BaseModel):
    """Represents an MCP resource access"""
    server_name: str = Field(..., description="The name of the MCP server")
    uri: str = Field(..., description="The URI of the resource to access") 