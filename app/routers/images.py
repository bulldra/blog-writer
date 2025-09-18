from __future__ import annotations

import base64
import html
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EyecatchRequest(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    width: int = 1200
    height: int = 630
    theme: Optional[str] = None  # 例: "dark" | "light" | None


def _build_svg(title: str, width: int, height: int, theme: Optional[str]) -> str:
    bg1 = "#111827" if theme == "dark" else "#2563eb"
    bg2 = "#1f2937" if theme == "dark" else "#60a5fa"
    fg = "#e5e7eb" if theme == "dark" else "#ffffff"
    safe_title = html.escape(title)[:120]
    # 中央寄せ、適当なラップ
    lines = []
    words = safe_title.split()
    cur = ""
    for w in words or [safe_title]:
        nxt = (cur + " " + w).strip()
        if len(nxt) > 20 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    if not lines:
        lines = [safe_title or "Untitled"]

    line_height = 72
    start_y = height // 2 - (len(lines) - 1) * (line_height // 2)
    text_elems = []
    for i, ln in enumerate(lines):
        y = start_y + i * line_height
        text_elems.append(
            f'<text x="50%" y="{y}" text-anchor="middle" '
            f'font-family="ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial" '
            f'font-size="56" fill="{fg}" opacity="0.95">{ln}</text>'
        )

    svg = f"""
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">
  <defs>
    <linearGradient id=\"g\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"> 
      <stop offset=\"0%\" stop-color=\"{bg1}\"/>
      <stop offset=\"100%\" stop-color=\"{bg2}\"/>
    </linearGradient>
  </defs>
  <rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"url(#g)\"/>
  <g>
    {"".join(text_elems)}
  </g>
  <rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"none\" stroke=\"rgba(255,255,255,0.2)\"/>
  <text x=\"96\" y=\"{height - 48}\" fill=\"rgba(255,255,255,0.7)\" font-size=\"22\" font-family=\"ui-sans-serif, system-ui\">blog-writer</text>
</svg>
""".strip()
    return svg


@router.post("/eyecatch")
def generate_eyecatch(req: EyecatchRequest):
    width = min(max(int(req.width or 1200), 600), 1600)
    height = min(max(int(req.height or 630), 315), 1200)
    title = (req.title or req.prompt or "Blog Post").strip()
    svg = _build_svg(title, width, height, (req.theme or None))
    # データURL（utf8）
    # SVG は URL エンコードよりも base64 の方が互換性が高いケースがある
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    data_url = f"data:image/svg+xml;base64,{b64}"
    return {"data_url": data_url, "content_type": "image/svg+xml"}
