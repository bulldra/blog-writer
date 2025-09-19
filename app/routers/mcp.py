"""MCP API routes."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp_util import GenericMCPClient, test_mcp_connection
from app.storage import (
    add_mcp_server,
    get_mcp_settings,
    remove_mcp_server,
    save_mcp_settings,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class MCPServerConfig(BaseModel):
    """MCP server configuration model."""

    name: str = Field(..., description="Display name for the MCP server")
    command: str = Field(..., description="Command to start the MCP server")
    args: List[str] = Field(default=[], description="Arguments for the MCP server")
    env: Dict[str, str] = Field(default={}, description="Environment variables")
    enabled: bool = Field(default=False, description="Whether this server is enabled")


class MCPSettings(BaseModel):
    """MCP settings model."""

    servers: Dict[str, MCPServerConfig] = Field(
        default={}, description="Dictionary of MCP server configurations"
    )
    enabled: bool = Field(default=False, description="Whether MCP integration is enabled")


class MCPTestRequest(BaseModel):
    """Request model for testing MCP server connection."""

    server_id: str = Field(..., description="ID of the server to test")


class MCPToolCallRequest(BaseModel):
    """Request model for calling MCP tools."""

    server_id: str = Field(..., description="ID of the MCP server")
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default={}, description="Arguments for the tool")


@router.get("/settings")
async def get_settings() -> MCPSettings:
    """Get MCP settings."""
    try:
        settings = get_mcp_settings()
        
        # Convert server configs to Pydantic models
        servers = {}
        for server_id, config in settings.get("servers", {}).items():
            servers[server_id] = MCPServerConfig(**config)
        
        return MCPSettings(
            servers=servers,
            enabled=settings.get("enabled", False)
        )
    except Exception as e:
        logger.error(f"Error getting MCP settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get MCP settings")


@router.post("/settings")
async def save_settings(settings: MCPSettings) -> Dict[str, str]:
    """Save MCP settings."""
    try:
        # Convert Pydantic models to dictionaries for storage
        servers = {}
        for server_id, config in settings.servers.items():
            servers[server_id] = config.model_dump()
        
        save_mcp_settings(servers=servers, enabled=settings.enabled)
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Error saving MCP settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save MCP settings")


@router.post("/servers/{server_id}")
async def add_server(server_id: str, config: MCPServerConfig) -> Dict[str, str]:
    """Add or update an MCP server configuration."""
    try:
        add_mcp_server(
            server_id=server_id,
            name=config.name,
            command=config.command,
            args=config.args,
            env=config.env,
            enabled=config.enabled,
        )
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Error adding MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add MCP server")


@router.delete("/servers/{server_id}")
async def delete_server(server_id: str) -> Dict[str, str]:
    """Delete an MCP server configuration."""
    try:
        if remove_mcp_server(server_id):
            return {"status": "deleted"}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete MCP server")


@router.post("/test-connection")
async def test_connection(request: MCPTestRequest) -> Dict[str, Any]:
    """Test connection to an MCP server."""
    try:
        settings = get_mcp_settings()
        servers = settings.get("servers", {})
        
        if request.server_id not in servers:
            raise HTTPException(status_code=404, detail="Server not found")
        
        server_config = servers[request.server_id]
        success = await test_mcp_connection(server_config)
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing MCP connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to test MCP connection")


@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: str) -> Dict[str, Any]:
    """List available tools for an MCP server."""
    try:
        settings = get_mcp_settings()
        servers = settings.get("servers", {})
        
        if server_id not in servers:
            raise HTTPException(status_code=404, detail="Server not found")
        
        server_config = servers[server_id]
        
        if not server_config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Server is not enabled")
        
        async with GenericMCPClient(server_config) as client:
            tools = await client.list_tools()
            return {"tools": tools}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tools for server {server_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tools")


@router.post("/call-tool")
async def call_tool(request: MCPToolCallRequest) -> Dict[str, Any]:
    """Call a tool on an MCP server."""
    try:
        settings = get_mcp_settings()
        servers = settings.get("servers", {})
        
        if request.server_id not in servers:
            raise HTTPException(status_code=404, detail="Server not found")
        
        server_config = servers[request.server_id]
        
        if not server_config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Server is not enabled")
        
        async with GenericMCPClient(server_config) as client:
            result = await client.call_tool(request.tool_name, request.arguments)
            return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling tool {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to call tool")