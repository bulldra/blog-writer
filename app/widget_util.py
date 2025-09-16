"""Widget processing utilities for blog writer."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.notion_util import NotionMCPClient, format_notion_page_for_context
from app.storage import get_notion_settings

logger = logging.getLogger(__name__)


async def process_notion_widget(widget_data: Dict[str, Any]) -> Optional[str]:
    """Process Notion widget and return context data.

    Args:
        widget_data: Widget configuration containing Notion settings

    Returns:
        Formatted context string or None if failed
    """
    try:
        notion_settings = get_notion_settings()

        if not notion_settings.get("enabled", False):
            logger.warning("Notion integration is disabled")
            return None

        if not notion_settings.get("env", {}).get("NOTION_API_KEY"):
            logger.warning("Notion API key is not configured")
            return None

        # ウィジェット設定から必要な情報を取得
        page_ids = widget_data.get("page_ids", [])
        search_query = widget_data.get("search_query", "")
        max_pages = min(widget_data.get("max_pages", 5), 10)

        context_parts = []

        async with NotionMCPClient(notion_settings) as client:
            # 指定されたページIDから情報を取得
            if page_ids:
                for page_id in page_ids[:max_pages]:
                    try:
                        page = await client.get_page_content(page_id)
                        if page:
                            context = format_notion_page_for_context(page)
                            context_parts.append(context)
                    except Exception as e:
                        logger.error(f"Failed to get page {page_id}: {e}")

            # 検索クエリがある場合は検索も実行
            elif search_query:
                try:
                    pages = await client.search_pages(search_query, max_pages)
                    for page in pages:
                        context = format_notion_page_for_context(page)
                        context_parts.append(context)
                except Exception as e:
                    logger.error(f"Failed to search pages: {e}")

        if context_parts:
            return "\n\n---\n\n".join(context_parts)
        else:
            return None

    except Exception as e:
        logger.error(f"Error processing Notion widget: {e}")
        return None


def process_widget_sync(widget_type: str, widget_data: Dict[str, Any]) -> Optional[str]:
    """Synchronous wrapper for widget processing.

    Args:
        widget_type: Type of widget to process
        widget_data: Widget configuration data

    Returns:
        Processed widget context or None if failed
    """
    if widget_type == "notion":
        # Validate configuration first
        if not validate_widget_config(widget_type, widget_data):
            return None

        try:
            # Check if we're already in an event loop
            try:
                asyncio.get_running_loop()
                # If we're in a loop, we can't create a new one
                logger.warning(
                    "Cannot process Notion widget in sync mode while in async context"
                )
                return None
            except RuntimeError:
                # No running loop, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(process_notion_widget(widget_data))
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"Error in sync widget processing: {e}")
            return None

    # 他のウィジェットタイプは既存の処理を継続
    return None


async def process_widgets_async(widgets: List[Dict[str, Any]]) -> Dict[str, str]:
    """Process multiple widgets asynchronously.

    Args:
        widgets: List of widget configurations

    Returns:
        Dictionary mapping widget IDs to their context data
    """
    results = {}

    for widget in widgets:
        widget_type = widget.get("type", "")
        widget_id = widget.get("id", "")
        widget_data = widget.get("data", {})

        if widget_type == "notion":
            context = await process_notion_widget(widget_data)
            if context:
                results[widget_id] = context

        # 他のウィジェットタイプは既存の処理で対応

    return results


def get_widget_default_config(widget_type: str) -> Dict[str, Any]:
    """Get default configuration for a widget type.

    Args:
        widget_type: Type of widget

    Returns:
        Default configuration dictionary
    """
    if widget_type == "notion":
        return {
            "page_ids": [],
            "search_query": "",
            "max_pages": 5,
        }

    return {}


def validate_widget_config(widget_type: str, widget_data: Dict[str, Any]) -> bool:
    """Validate widget configuration.

    Args:
        widget_type: Type of widget
        widget_data: Widget configuration data

    Returns:
        True if configuration is valid, False otherwise
    """
    if widget_type == "notion":
        page_ids = widget_data.get("page_ids", [])
        search_query = widget_data.get("search_query", "")

        # ページIDまたは検索クエリのいずれかが必要
        if not page_ids and not search_query:
            return False

        # ページIDの形式をチェック
        if page_ids:
            if not isinstance(page_ids, list):
                return False
            for page_id in page_ids:
                if not isinstance(page_id, str) or not page_id.strip():
                    return False

        # 検索クエリの形式をチェック
        if search_query and not isinstance(search_query, str):
            return False

        return True

    return True
