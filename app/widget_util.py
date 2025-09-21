"""Widget processing utilities for blog writer."""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar

import httpx

from app.ai_utils import extract_text
from app.mcp_util import GenericMCPClient, format_mcp_tool_result
from app.notion_util import NotionMCPClient, format_notion_page_for_context
from app.security import is_url_allowed
from app.storage import get_mcp_settings, get_notion_settings

logger = logging.getLogger(__name__)


T = TypeVar("T")


def _has_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def _run_coro_sync(factory: Callable[[], Awaitable[T]]) -> Optional[T]:
    if _has_running_loop():
        logger.warning("Cannot run in sync mode inside async context")
        return None
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(factory())
    except Exception as e:  # noqa: BLE001
        logger.error("Error running coroutine sync: %s", e)
        return None
    finally:
        try:
            loop.close()
        except Exception:  # noqa: BLE001
            pass


def _process_text_sync(widget_type: str, widget_data: Dict[str, Any]) -> Optional[str]:
    if not validate_widget_config(widget_type, widget_data):
        return None
    if widget_type == "notion":
        return _run_coro_sync(lambda: process_notion_widget(widget_data))
    if widget_type == "mcp":
        return _run_coro_sync(lambda: process_mcp_widget(widget_data))
    if widget_type == "url_context":
        return _run_coro_sync(lambda: process_url_context_widget(widget_data))
    if widget_type == "x":
        try:
            return process_x_widget(widget_data)
        except Exception as e:  # noqa: BLE001
            logger.error("Error processing x widget: %s", e)
            return None
    if widget_type == "scrape":
        try:
            text, _shot = _scrape_with_selenium_wrapper(widget_data)
            return text
        except Exception as e:  # noqa: BLE001
            logger.error("Error in sync scrape: %s", e)
            return None
    return None


def _process_text_media_sync(
    widget_type: str, widget_data: Dict[str, Any]
) -> Tuple[Optional[str], List[Tuple[str, bytes]]]:
    if not validate_widget_config(widget_type, widget_data):
        return None, []
    media: List[Tuple[str, bytes]] = []
    if widget_type == "notion":
        text = _run_coro_sync(lambda: process_notion_widget(widget_data))
        return text, media
    if widget_type == "url_context":
        text = _run_coro_sync(lambda: process_url_context_widget(widget_data))
        return text, media
    if widget_type == "x":
        try:
            text = process_x_widget(widget_data)
            return text, media
        except Exception as e:  # noqa: BLE001
            logger.error("Error in sync x: %s", e)
            return None, []
    if widget_type == "scrape":
        try:
            text, shot = _scrape_with_selenium_wrapper(widget_data)
            if shot:
                media.append(("image/png", shot))
            return text, media
        except Exception as e:  # noqa: BLE001
            logger.error("Error in sync scrape: %s", e)
            return None, []
    if widget_type == "mcp":
        text = _run_coro_sync(lambda: process_mcp_widget(widget_data))
        return text, media
    return None, []


async def process_mcp_widget(widget_data: Dict[str, Any]) -> Optional[str]:
    """Process MCP widget and return context data.

    Args:
        widget_data: Widget configuration containing MCP settings

    Returns:
        Formatted context string or None if failed
    """
    try:
        mcp_settings = get_mcp_settings()

        if not mcp_settings.get("enabled", False):
            logger.warning("MCP integration is disabled")
            return None

        # ウィジェット設定から必要な情報を取得
        server_id = widget_data.get("server_id", "")
        tool_name = widget_data.get("tool_name", "")
        arguments = widget_data.get("arguments", {})

        if not server_id or not tool_name:
            logger.warning("MCP widget: server_id and tool_name are required")
            return None

        servers = mcp_settings.get("servers", {})
        if server_id not in servers:
            logger.warning(f"MCP server not found: {server_id}")
            return None

        server_config = servers[server_id]
        if not server_config.get("enabled", False):
            logger.warning(f"MCP server is disabled: {server_id}")
            return None

        async with GenericMCPClient(server_config) as client:
            result = await client.call_tool(tool_name, arguments)
            if result:
                server_name = server_config.get("name", server_id)
                return format_mcp_tool_result(result, tool_name, server_name)
            else:
                logger.warning(f"MCP tool returned no result: {tool_name}")
                return None

    except Exception as e:
        logger.error(f"Error processing MCP widget: {e}")
        return None


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


async def process_url_context_widget(widget_data: Dict[str, Any]) -> Optional[str]:
    """Fetch URL content safely and return extracted text."""
    try:
        url = str(widget_data.get("url", "")).strip()
        if not url or not is_url_allowed(url):
            return None
        timeout = httpx.Timeout(8.0, connect=4.0)
        headers = {"User-Agent": "BlogWriter/1.0"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "").lower()
            if "text/html" in ctype or "text/plain" in ctype or not ctype:
                body = resp.text[: 2048 * 1024]
                text = extract_text(body) or ""
                text = text.strip()
                if not text:
                    return None
                max_chars = int(widget_data.get("max_chars", 8000))
                max_chars = max(500, min(20000, max_chars))
                return text[:max_chars]
            return None
    except Exception as e:
        logger.error(f"Error processing url_context widget: {e}")
        return None


def process_widget_sync(widget_type: str, widget_data: Dict[str, Any]) -> Optional[str]:
    return _process_text_sync(widget_type, widget_data)


def process_widget_with_media(
    widget_type: str, widget_data: Dict[str, Any]
) -> Tuple[Optional[str], List[Tuple[str, bytes]]]:
    return _process_text_media_sync(widget_type, widget_data)


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

        if widget_type == "mcp":
            context = await process_mcp_widget(widget_data)
            if context:
                results[widget_id] = context

        if widget_type == "url_context":
            context = await process_url_context_widget(widget_data)
            if context:
                results[widget_id] = context

        if widget_type == "x":
            try:
                text = process_x_widget(widget_data)
                if text:
                    results[widget_id] = text
            except Exception as e:  # noqa: BLE001
                logger.error("Error processing x widget async: %s", e)

        if widget_type == "scrape":
            try:
                text, _shot = await asyncio.to_thread(
                    _scrape_with_selenium_wrapper, widget_data
                )
                if text:
                    results[widget_id] = text
            except Exception as e:  # noqa: BLE001
                logger.error("Error processing scrape widget async: %s", e)

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

    if widget_type == "url_context":
        return {
            "url": "",
            "max_chars": 8000,
        }

    if widget_type == "scrape":
        return {
            "url": "",
            "selector": "body",
            "mode": "text",  # text | screenshot | both
            "timeout_ms": 8000,
            "headless": True,
            "viewport": {"width": 1200, "height": 800},
        }

    if widget_type == "mcp":
        return {
            "server_id": "",
            "tool_name": "",
            "arguments": {},
        }

    if widget_type == "x":
        return {
            # 実運用では URL/ユーザー/スレッドID 等を使う想定。
            # テストでは raw_posts 入力（ローカル整形）を利用。
            "url": "",
            "mode": "thread",  # thread | user
            "max_posts": 20,
            "raw_posts": [],  # [{id, text, author, created_at}] for test
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

    if widget_type == "url_context":
        url = widget_data.get("url", "")
        if not isinstance(url, str) or not url.strip():
            return False
        return is_url_allowed(url)

    if widget_type == "scrape":
        url = widget_data.get("url", "")
        if not isinstance(url, str) or not url.strip():
            return False
        if not is_url_allowed(url):
            return False
        sel = widget_data.get("selector", "body")
        if not isinstance(sel, str) or not sel.strip():
            return False
        mode = widget_data.get("mode", "text")
        if mode not in ("text", "screenshot", "both"):
            return False
        try:
            _ = int(widget_data.get("timeout_ms", 8000))
        except Exception:
            return False
        vp = widget_data.get("viewport", {"width": 1200, "height": 800})
        if not isinstance(vp, dict):
            return False
        if not isinstance(vp.get("width", 1200), int):
            return False
        if not isinstance(vp.get("height", 800), int):
            return False
        return True

    if widget_type == "mcp":
        server_id = widget_data.get("server_id", "")
        tool_name = widget_data.get("tool_name", "")

        # server_idとtool_nameは必須
        if not isinstance(server_id, str) or not server_id.strip():
            return False
        if not isinstance(tool_name, str) or not tool_name.strip():
            return False

        # argumentsは辞書である必要がある
        arguments = widget_data.get("arguments", {})
        if not isinstance(arguments, dict):
            return False

        return True

    if widget_type == "x":
        # raw_posts があればそれだけでOK（ネットワーク不要のテスト用）
        raw = widget_data.get("raw_posts", [])
        if isinstance(raw, list) and raw:
            for it in raw:
                if not isinstance(it, dict):
                    return False
                if not isinstance(it.get("text", ""), str):
                    return False
            return True
        # URL がある場合は形式とドメインを軽く確認
        url = widget_data.get("url", "")
        if isinstance(url, str) and url.strip():
            # Xは is_url_allowed で基本チェック（private/loopback防止）
            return is_url_allowed(url)
        # どちらも無ければ無効
        return False

    return True


def _format_x_posts(raw_posts: List[Dict[str, Any]], max_posts: int = 50) -> str:
    lines: List[str] = []
    cnt = 0
    for it in raw_posts:
        if cnt >= max_posts:
            break
        text = str(it.get("text", "")).strip()
        if not text:
            continue
        author = str(it.get("author", "")).strip() or "unknown"
        created = str(it.get("created_at", "")).strip()
        prefix = f"@{author}"
        if created:
            prefix += f" ({created})"
        lines.append(prefix)
        # 本文は引用形式に
        for ln in text.splitlines():
            ln = ln.strip()
            if ln:
                lines.append(f"> {ln}")
        lines.append("")
        cnt += 1
    return "\n".join(lines).strip()


def process_x_widget(widget_data: Dict[str, Any]) -> Optional[str]:
    """Process X widget.

    優先: raw_posts によるローカル整形（テスト用）。
    それ以外（URLなど）は将来的に対応。現時点では None を返す。
    """
    raw = widget_data.get("raw_posts", [])
    if isinstance(raw, list) and raw:
        max_posts = int(widget_data.get("max_posts", 20))
        max_posts = max(1, min(100, max_posts))
        text = _format_x_posts(raw, max_posts=max_posts)
        return text or None
    # TODO: URL/ユーザータイムライン取得などは将来実装
    return None


def _scrape_with_selenium_wrapper(
    widget_data: Dict[str, Any],
) -> Tuple[Optional[str], Optional[bytes]]:
    url = str(widget_data.get("url", "")).strip()
    selector = str(widget_data.get("selector", "body")).strip() or "body"
    mode = str(widget_data.get("mode", "text")).strip()
    timeout_ms = int(widget_data.get("timeout_ms", 8000))
    headless = bool(widget_data.get("headless", True))
    vp = widget_data.get("viewport", {"width": 1200, "height": 800}) or {}
    width = int(vp.get("width", 1200))
    height = int(vp.get("height", 800))
    return _scrape_with_selenium(
        url, selector, mode, timeout_ms, headless, width, height
    )


def _scrape_with_selenium(
    url: str,
    selector: str,
    mode: str,
    timeout_ms: int,
    headless: bool,
    width: int,
    height: int,
) -> Tuple[Optional[str], Optional[bytes]]:
    try:
        import importlib

        webdriver_mod = importlib.import_module("selenium.webdriver")
        chrome_opts_mod = importlib.import_module("selenium.webdriver.chrome.options")
        by_mod = importlib.import_module("selenium.webdriver.common.by")
        ec_mod = importlib.import_module(
            "selenium.webdriver.support.expected_conditions"
        )
        ui_mod = importlib.import_module("selenium.webdriver.support.ui")

        from typing import Any as _Any

        Options: _Any = getattr(chrome_opts_mod, "Options", None)
        By: _Any = getattr(by_mod, "By", None)
        WebDriverWait: _Any = getattr(ui_mod, "WebDriverWait", None)
        Chrome: _Any = getattr(webdriver_mod, "Chrome", None)
        if not all([Options, By, WebDriverWait, Chrome]):
            raise RuntimeError("Selenium components not available")
    except Exception as e:
        logger.error("Selenium not available: %s", e)
        return None, None

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={width},{height}")

    driver = None
    try:
        driver = Chrome(options=opts)
        driver.set_window_size(width, height)
        driver.get(url)
        WebDriverWait(driver, max(1, int(timeout_ms / 1000))).until(
            ec_mod.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        text: Optional[str] = None
        screenshot: Optional[bytes] = None
        if mode in ("text", "both"):
            html = driver.page_source or ""
            text = (extract_text(html) or "").strip()[:20000]
        if mode in ("screenshot", "both"):
            try:
                screenshot = driver.get_screenshot_as_png()
            except Exception:
                screenshot = None
        return text, screenshot
    except Exception as e:
        logger.error("Selenium scrape error: %s", e)
        return None, None
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass
