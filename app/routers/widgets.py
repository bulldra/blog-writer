from __future__ import annotations

import base64
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.widget_util import (
    _scrape_with_selenium_wrapper,
    process_x_widget,
    validate_widget_config,
)

router = APIRouter()


class Viewport(BaseModel):
    width: int = 1200
    height: int = 800


class ScrapePreviewRequest(BaseModel):
    url: str
    selector: str = "body"
    mode: str = "text"  # text | screenshot | both
    timeout_ms: int = 8000
    headless: bool = True
    viewport: Viewport = Viewport()


@router.post("/scrape/preview")
def scrape_preview(req: ScrapePreviewRequest) -> Dict[str, Any]:
    data = {
        "url": req.url,
        "selector": req.selector,
        "mode": req.mode,
        "timeout_ms": req.timeout_ms,
        "headless": req.headless,
        "viewport": {"width": req.viewport.width, "height": req.viewport.height},
    }
    if not validate_widget_config("scrape", data):
        raise HTTPException(status_code=400, detail="invalid scrape config")

    text: Optional[str]
    shot: Optional[bytes]
    text, shot = _scrape_with_selenium_wrapper(data)
    if text is None and shot is None:
        # 取得失敗
        return {"ok": False, "error": "scrape_failed"}

    out: Dict[str, Any] = {"ok": True}
    if text:
        # 長すぎる場合は軽く切り詰め
        out["text"] = text[:4000]
    if shot:
        b64 = base64.b64encode(shot).decode("ascii")
        out["image_data_url"] = f"data:image/png;base64,{b64}"
    return out


class XRawPost(BaseModel):
    id: str | None = None
    text: str
    author: str | None = None
    created_at: str | None = None


class XPreviewRequest(BaseModel):
    # 実運用では url などが来る想定。テストでは raw_posts 経由。
    url: str | None = None
    mode: str = "thread"
    max_posts: int = 20
    raw_posts: list[XRawPost] | None = None


@router.post("/x/preview")
def x_preview(req: XPreviewRequest) -> Dict[str, Any]:
    data = {
        "url": req.url or "",
        "mode": req.mode,
        "max_posts": req.max_posts,
        "raw_posts": [p.model_dump() for p in (req.raw_posts or [])],
    }
    if not validate_widget_config("x", data):
        raise HTTPException(status_code=400, detail="invalid x config")
    text = process_x_widget(data)
    if not text:
        return {"ok": False, "error": "x_preview_failed"}
    return {"ok": True, "text": text}
