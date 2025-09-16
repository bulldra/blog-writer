"""Notion MCP API routes."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.notion_util import (
    NotionMCPClient,
    format_notion_page_for_context,
    test_notion_connection,
)
from app.storage import get_notion_settings, save_notion_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class NotionMCPSettings(BaseModel):
    """Notion MCP settings model."""

    command: str = Field(default="npx", description="MCP server command")
    args: List[str] = Field(
        default=["@modelcontextprotocol/server-notion"],
        description="MCP server arguments",
    )
    env: Dict[str, str] = Field(
        default={"NOTION_API_KEY": ""}, description="Environment variables"
    )
    enabled: bool = Field(
        default=False, description="Whether Notion integration is enabled"
    )
    default_parent_id: str = Field(
        default="", description="Default parent page ID for new pages"
    )


class NotionPageRequest(BaseModel):
    """Request model for creating Notion pages."""

    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content in markdown")
    parent_id: Optional[str] = Field(None, description="Parent page ID")


class NotionSearchRequest(BaseModel):
    """Request model for searching Notion pages."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")


@router.get("/settings")
async def get_settings() -> NotionMCPSettings:
    """Get Notion MCP settings."""
    try:
        settings = get_notion_settings()
        return NotionMCPSettings(**settings)
    except Exception as e:
        logger.error(f"Error getting Notion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Notion settings")


@router.post("/settings")
async def save_settings(settings: NotionMCPSettings) -> Dict[str, str]:
    """Save Notion MCP settings."""
    try:
        save_notion_settings(
            command=settings.command,
            args=settings.args,
            env=settings.env,
            enabled=settings.enabled,
            default_parent_id=settings.default_parent_id,
        )
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Error saving Notion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save Notion settings")


@router.post("/test-connection")
async def test_connection() -> Dict[str, Any]:
    """Test connection to Notion MCP server."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            return {"connected": False, "error": "Notion integration is disabled"}

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            return {"connected": False, "error": "Notion API key is not configured"}

        success = await test_notion_connection(settings)

        if success:
            return {"connected": True}
        else:
            return {
                "connected": False,
                "error": "Failed to connect to Notion MCP server",
            }

    except Exception as e:
        logger.error(f"Error testing Notion connection: {e}")
        return {"connected": False, "error": str(e)}


@router.get("/pages")
async def list_pages(limit: int = 10) -> List[Dict[str, Any]]:
    """List pages from Notion."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        async with NotionMCPClient(settings) as client:
            pages = await client.list_pages(limit=min(limit, 50))
            return pages

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Notion pages: {e}")
        raise HTTPException(status_code=500, detail="Failed to list Notion pages")


@router.get("/pages/{page_id}")
async def get_page(page_id: str) -> Dict[str, Any]:
    """Get a specific Notion page."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        async with NotionMCPClient(settings) as client:
            page = await client.get_page_content(page_id)

            if page is None:
                raise HTTPException(status_code=404, detail="Page not found")

            return page

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Notion page: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Notion page")


@router.post("/search")
async def search_pages(request: NotionSearchRequest) -> List[Dict[str, Any]]:
    """Search pages in Notion."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        async with NotionMCPClient(settings) as client:
            pages = await client.search_pages(request.query, request.limit)
            return pages

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching Notion pages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search Notion pages")


@router.post("/create-page")
async def create_page(request: NotionPageRequest) -> Dict[str, Any]:
    """Create a new page in Notion."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        # デフォルトの親ページIDを使用（指定されていない場合）
        parent_id = request.parent_id or settings.get("default_parent_id")

        async with NotionMCPClient(settings) as client:
            page = await client.create_page(request.title, request.content, parent_id)

            if page is None:
                raise HTTPException(status_code=500, detail="Failed to create page")

            return page

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Notion page: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Notion page")


@router.get("/pages/{page_id}/context")
async def get_page_context(page_id: str) -> Dict[str, str]:
    """Get formatted page content for use as context in article generation."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        async with NotionMCPClient(settings) as client:
            page = await client.get_page_content(page_id)

            if page is None:
                raise HTTPException(status_code=404, detail="Page not found")

            context = format_notion_page_for_context(page)
            return {"context": context}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Notion page context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get page context")


@router.post("/publish-article")
async def publish_article(request: NotionPageRequest) -> Dict[str, Any]:
    """Publish generated article as a new page in Notion."""
    try:
        settings = get_notion_settings()

        if not settings.get("enabled", False):
            raise HTTPException(
                status_code=400, detail="Notion integration is disabled"
            )

        if not settings.get("env", {}).get("NOTION_API_KEY"):
            raise HTTPException(
                status_code=400, detail="Notion API key is not configured"
            )

        # デフォルトの親ページIDを使用（指定されていない場合）
        parent_id = request.parent_id or settings.get("default_parent_id")

        async with NotionMCPClient(settings) as client:
            page = await client.create_page(request.title, request.content, parent_id)

            if page is None:
                raise HTTPException(status_code=500, detail="Failed to publish article")

            return {
                "page_id": page.get("id", ""),
                "url": page.get("url", ""),
                "title": request.title,
                "status": "published",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing article to Notion: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish article")
