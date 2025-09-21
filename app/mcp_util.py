"""Generic MCP client utilities for blog writer."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp.client.client import Client, StdioTransport

logger = logging.getLogger(__name__)


class GenericMCPClient:
    """Generic MCP client for managing MCP server integrations."""

    def __init__(self, server_config: Dict[str, Any]):
        """Initialize the MCP client.

        Args:
            server_config: Dictionary containing MCP server configuration
        """
        self.config: Dict[str, Any] = server_config
        self._session: Optional[Any] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the MCP server."""
        try:
            transport = StdioTransport(
                command=self.config.get("command", "npx"),
                args=self.config.get("args", []),
                env=self.config.get("env", {}),
            )

            client = Client(transport=transport, name="generic-mcp")
            self._session = await client.__aenter__()
            logger.info(
                f"Connected to MCP server: {self.config.get('name', 'unknown')}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.warning(f"Error during MCP disconnect: {e}")
            finally:
                self._session = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            result = await self._session.list_tools()
            return result.tools if hasattr(result, "tools") else []
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[str]:
        """Call a tool on the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            result = await self._session.call_tool(name=tool_name, arguments=arguments)
            if hasattr(result, "content") and result.content:
                # Extract text from tool result
                content = result.content
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if hasattr(first_item, "text"):
                        return str(first_item.text)
                    elif isinstance(first_item, dict) and "text" in first_item:
                        return str(first_item["text"])
                elif isinstance(content, str):
                    return content
            return None
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None


def get_default_mcp_config() -> Dict[str, Any]:
    """Get default MCP configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "servers": {},
        "enabled": False,
    }


async def test_mcp_connection(server_config: Dict[str, Any]) -> bool:
    """Test connection to MCP server.

    Args:
        server_config: MCP server configuration

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with GenericMCPClient(server_config) as client:
            # 簡単なテスト：利用可能なツールを取得
            await client.list_tools()
            return True
    except Exception as e:
        logger.error(f"MCP connection test failed: {e}")
        return False


def format_mcp_tool_result(result: str, tool_name: str, server_name: str) -> str:
    """Format MCP tool result for context inclusion.

    Args:
        result: Tool execution result
        tool_name: Name of the called tool
        server_name: Name of the MCP server

    Returns:
        Formatted context string
    """
    return f"""## MCP Tool Result ({server_name})

**Tool:** {tool_name}

**Result:**
{result}

---
"""
