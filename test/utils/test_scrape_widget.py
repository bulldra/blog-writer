from typing import Any, Dict, Optional, Tuple

import pytest

from app import widget_util
from app.widget_util import (
    get_widget_default_config,
    process_widget_sync,
    validate_widget_config,
)


def test_get_widget_default_config_scrape() -> None:
    cfg = get_widget_default_config("scrape")
    assert cfg["url"] == ""
    assert cfg["selector"] == "body"
    assert cfg["mode"] in {"text", "screenshot", "both"}
    assert isinstance(cfg["timeout_ms"], int)
    assert isinstance(cfg["headless"], bool)
    vp = cfg["viewport"]
    assert isinstance(vp, dict)
    assert isinstance(vp.get("width"), int)
    assert isinstance(vp.get("height"), int)


def test_validate_widget_config_scrape_valid() -> None:
    valid: Dict[str, Any] = {
        "url": "https://example.com/",
        "selector": "main",
        "mode": "text",
        "timeout_ms": 5000,
        "headless": True,
        "viewport": {"width": 1000, "height": 800},
    }
    assert validate_widget_config("scrape", valid) is True


@pytest.mark.parametrize(
    "bad",
    [
        {"url": "", "selector": "main", "mode": "text"},
        {"url": "http://127.0.0.1/", "selector": "main", "mode": "text"},
        {"url": "https://example.com/", "selector": "", "mode": "text"},
        {"url": "https://example.com/", "selector": "main", "mode": "x"},
        {
            "url": "https://example.com/",
            "selector": "main",
            "mode": "text",
            "timeout_ms": "nope",
        },
        {
            "url": "https://example.com/",
            "selector": "main",
            "mode": "text",
            "viewport": {"width": "w", "height": 800},
        },
    ],
)
def test_validate_widget_config_scrape_invalid(bad: Dict[str, Any]) -> None:
    assert validate_widget_config("scrape", bad) is False


def test_process_widget_sync_scrape(monkeypatch: pytest.MonkeyPatch) -> None:
    called: Dict[str, Any] = {}

    def fake_wrapper(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes]]:
        called["data"] = data
        return "extracted text", b"\x89PNG..."

    monkeypatch.setattr(widget_util, "_scrape_with_selenium_wrapper", fake_wrapper)

    data: Dict[str, Any] = {
        "url": "https://example.com/",
        "selector": "article",
        "mode": "text",
        "timeout_ms": 3000,
        "headless": True,
        "viewport": {"width": 1200, "height": 800},
    }
    out = process_widget_sync("scrape", data)
    assert out == "extracted text"
    assert called["data"]["selector"] == "article"


@pytest.mark.asyncio
async def test_process_widgets_async_scrape(monkeypatch: pytest.MonkeyPatch) -> None:
    called: Dict[str, Any] = {}

    def fake_wrapper(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes]]:
        called["data"] = data
        return "async text", None

    monkeypatch.setattr(widget_util, "_scrape_with_selenium_wrapper", fake_wrapper)

    widgets = [
        {
            "id": "scr1",
            "type": "scrape",
            "data": {
                "url": "https://example.com/",
                "selector": "main",
                "mode": "text",
                "timeout_ms": 4000,
                "headless": True,
                "viewport": {"width": 1200, "height": 800},
            },
        }
    ]

    res = await widget_util.process_widgets_async(widgets)
    assert res.get("scr1") == "async text"
