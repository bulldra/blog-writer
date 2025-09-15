from __future__ import annotations

import html as html_mod
import re
from typing import List, Mapping, Optional, Protocol


class BulletsParams(Protocol):
    title: Optional[str]
    style: Optional[str]
    length: Optional[str]
    highlights: Optional[List[str]]
    highlights_asin: Optional[List[Optional[str]]]
    prompt_template: Optional[str]
    url_context: Optional[str]
    extra_context: Optional[Mapping[str, str]]


def extract_text(html: str) -> str:
    html = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = html_mod.unescape(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


def apply_prompt_template(template: str, context: Mapping[str, object]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip().lower()
        val = context.get(key, match.group(0))
        return str(val)

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template)


def build_bullets_prompt(req: BulletsParams, bullets: List[str]) -> str:
    title_line = f"タイトル案: {req.title}\n" if req.title else ""
    style_line = f"トーン/文体: {req.style}\n" if req.style else ""
    length_line = f"分量の目安: {req.length}\n" if req.length else ""
    bullets_block = "\n".join(f"- {b}" for b in bullets)
    base_prompt = (
        "以下の情報を踏まえて、日本語のブログ記事草稿を作成してください。\n\n"
        "[メタ情報]\n"
        f"{title_line}{style_line}{length_line}"
    )
    if req.url_context:
        base_prompt += f"参照URL: {req.url_context}\n"
    if bullets_block:
        base_prompt += "[入れ込みたい要素]\n" + bullets_block + "\n"
    if req.highlights:
        blocks: List[str] = []
        for idx, h in enumerate(req.highlights[:300]):
            if not h or not h.strip():
                continue
            asin: Optional[str] = None
            if req.highlights_asin and idx < len(req.highlights_asin or []):
                asin = req.highlights_asin[idx]
            block = f"> {h.strip()}"
            if asin:
                block += f"\n[asin:{asin}:detail]"
            blocks.append(block)
        htext = "\n\n".join(blocks)[:4000]
        if htext:
            base_prompt += "\n[参考引用（Markdown引用＋ASIN）]\n" + htext + "\n"
    if req.prompt_template and req.prompt_template.strip():
        bullets_str = bullets_block
        highlights_str = "\n".join(
            [f"- {h.strip()}" for h in (req.highlights or []) if h and h.strip()]
        )
        ctx: dict[str, object] = {
            "title": req.title or "",
            "style": req.style or "",
            "length": req.length or "",
            "bullets": bullets_str,
            "highlights": highlights_str,
            "base": base_prompt,
            "url_context": req.url_context or "",
        }
        # extra_context をそのまま埋め込み可能にする
        if req.extra_context:
            for k, v in req.extra_context.items():
                if isinstance(k, str):
                    ctx[k] = v
        return apply_prompt_template(req.prompt_template, ctx)
    return base_prompt
