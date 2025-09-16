"""Notion MCP client utilities for blog writer (fastmcp 版)。"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastmcp.client.client import Client, StdioTransport

logger = logging.getLogger(__name__)


# fastmcp を前提として直接利用


class NotionMCPClient:
    """Notion MCP client for managing Notion integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Notion MCP client.

        Args:
            config: Dictionary containing MCP server configuration
        """
        self.config: Dict[str, Any] = config
        self._session: Optional[Any] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the Notion MCP server."""
        try:
            transport = StdioTransport(
                command=self.config.get("command", "npx"),
                args=self.config.get("args", ["@modelcontextprotocol/server-notion"]),
                env=self.config.get("env", {}),
            )

            # クライアント開始（async context manager を open）
            client = Client(transport=transport, name="notion-mcp")
            self._session = await client.__aenter__()
            logger.info("Connected to Notion MCP server")

        except Exception as e:
            logger.error(f"Failed to connect to Notion MCP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the Notion MCP server."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
                self._session = None
                logger.info("Disconnected from Notion MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from Notion MCP server: {e}")

    async def list_pages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List pages from Notion.

        Args:
            limit: Maximum number of pages to retrieve

        Returns:
            List of page information dictionaries
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            # Notion ページ一覧取得ツールを呼び出し
            result = await self._session.call_tool("search_pages", {"limit": limit})

            if isinstance(result.content, list) and result.content:
                content_item = result.content[0]
                if hasattr(content_item, "text"):
                    try:
                        pages_data = json.loads(getattr(content_item, "text", ""))
                    except Exception:
                        return []
                    results = (
                        pages_data.get("results", [])
                        if isinstance(pages_data, dict)
                        else []
                    )
                    if isinstance(results, list):
                        rows: List[Dict[str, Any]] = []
                        for it in results:
                            if isinstance(it, dict):
                                rows.append(it)
                        return rows

            return []

        except Exception as e:
            logger.error(f"Failed to list Notion pages: {e}")
            return []

    async def get_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get content of a specific Notion page.

        Args:
            page_id: Notion page ID

        Returns:
            Page content dictionary or None if failed
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            # Notion ページ内容取得ツールを呼び出し
            result = await self._session.call_tool("get_page", {"page_id": page_id})

            if isinstance(result.content, list) and result.content:
                content_item = result.content[0]
                if hasattr(content_item, "text"):
                    try:
                        data = json.loads(getattr(content_item, "text", ""))
                    except Exception:
                        return None
                    if isinstance(data, dict):
                        return data

            return None

        except Exception as e:
            logger.error(f"Failed to get Notion page content: {e}")
            return None

    async def search_pages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search pages in Notion.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching page information
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            # Notion ページ検索ツールを呼び出し
            result = await self._session.call_tool(
                "search_pages", {"query": query, "limit": limit}
            )

            if isinstance(result.content, list) and result.content:
                content_item = result.content[0]
                if hasattr(content_item, "text"):
                    try:
                        search_data = json.loads(getattr(content_item, "text", ""))
                    except Exception:
                        return []
                    results = (
                        search_data.get("results", [])
                        if isinstance(search_data, dict)
                        else []
                    )
                    if isinstance(results, list):
                        rows: List[Dict[str, Any]] = []
                        for it in results:
                            if isinstance(it, dict):
                                rows.append(it)
                        return rows

            return []

        except Exception as e:
            logger.error(f"Failed to search Notion pages: {e}")
            return []

    async def create_page(
        self, title: str, content: str, parent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new page in Notion.

        Args:
            title: Page title
            content: Page content (markdown format)
            parent_id: Parent page ID (optional)

        Returns:
            Created page information or None if failed
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            # ページ作成のパラメータを準備
            create_params = {
                "title": title,
                "content": content,
            }
            if parent_id:
                create_params["parent_id"] = parent_id

            # Notion ページ作成ツールを呼び出し
            result = await self._session.call_tool("create_page", create_params)

            if isinstance(result.content, list) and result.content:
                content_item = result.content[0]
                if hasattr(content_item, "text"):
                    try:
                        data = json.loads(getattr(content_item, "text", ""))
                    except Exception:
                        return None
                    if isinstance(data, dict):
                        return data

            return None

        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            return None


def get_default_notion_config() -> Dict[str, Any]:
    """Get default Notion MCP configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {
            "NOTION_API_KEY": "",
        },
        "enabled": False,
    }


async def test_notion_connection(config: Dict[str, Any]) -> bool:
    """Test connection to Notion MCP server.

    Args:
        config: Notion MCP configuration

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with NotionMCPClient(config) as client:
            # 簡単なテスト：ページ一覧を取得
            await client.list_pages(limit=1)
            return True
    except Exception as e:
        logger.error(f"Notion connection test failed: {e}")
        return False


def format_notion_page_for_context(page: Dict[str, Any]) -> str:
    """Format Notion page data for use as context in article generation.

    Args:
        page: Page data from Notion

    Returns:
        Formatted string for context
    """
    title = page.get("properties", {}).get("title", {}).get("title", [])
    if title and isinstance(title, list) and title[0].get("plain_text"):
        page_title = title[0]["plain_text"]
    else:
        page_title = "Untitled"

    # ページのプロパティを取得
    properties = page.get("properties", {})
    formatted_props = []

    for prop_name, prop_data in properties.items():
        if prop_name == "title":
            continue

        prop_type = prop_data.get("type", "")
        prop_value = ""

        if prop_type == "rich_text" and prop_data.get("rich_text"):
            prop_value = " ".join(
                [item.get("plain_text", "") for item in prop_data["rich_text"]]
            )
        elif prop_type == "select" and prop_data.get("select"):
            prop_value = prop_data["select"].get("name", "")
        elif prop_type == "multi_select" and prop_data.get("multi_select"):
            prop_value = ", ".join(
                [item.get("name", "") for item in prop_data["multi_select"]]
            )
        elif prop_type == "date" and prop_data.get("date"):
            prop_value = prop_data["date"].get("start", "")

        if prop_value:
            formatted_props.append(f"{prop_name}: {prop_value}")

    result = f"## {page_title}\n"
    if formatted_props:
        result += "\n### プロパティ\n"
        for prop in formatted_props:
            result += f"- {prop}\n"

    # ページのコンテンツがある場合は追加
    if "content" in page and page["content"]:
        result += f"\n### コンテンツ\n{page['content']}\n"

    return result
