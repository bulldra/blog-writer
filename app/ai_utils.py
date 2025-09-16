from __future__ import annotations

import html as html_mod
import logging
import re
from typing import List, Mapping, Optional, Protocol

_logger = logging.getLogger(__name__)


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


def generate_rag_query(prompt: str, title: Optional[str] = None) -> str:
    """プロンプトからRAG検索用のクエリを生成

    Args:
        prompt: 生成プロンプト
        title: タイトル（オプション）

    Returns:
        RAG検索用のクエリ文字列
    """
    # プロンプトから検索に有用なキーワードを抽出
    search_terms = []

    # タイトルがある場合は追加
    if title:
        search_terms.append(title)

    # プロンプトから重要な名詞や概念を抽出（簡易的な実装）
    import_terms = re.findall(r"[一-龯ぁ-ゟァ-ヾ]+", prompt)
    meaningful_terms = [term for term in import_terms if len(term) >= 2]

    # 重複を除去して上位5つまで
    unique_terms = list(dict.fromkeys(meaningful_terms))[:5]
    search_terms.extend(unique_terms)

    # 検索クエリとして結合
    query = " ".join(search_terms)

    # 最大100文字に制限
    if len(query) > 100:
        query = query[:100]

    return query.strip()


def inject_rag_context(prompt: str, rag_context: str) -> str:
    """プロンプトにRAGコンテキストを注入

    Args:
        prompt: 元のプロンプト
        rag_context: RAG検索結果のコンテキスト

    Returns:
        RAGコンテキストが注入されたプロンプト
    """
    if not rag_context or rag_context.strip() == "関連する情報が見つかりませんでした。":
        return prompt

    # RAGコンテキストをプロンプトに挿入
    rag_section = f"\n\n[参考情報]\n{rag_context}\n\n上記の参考情報も踏まえて、"

    # プロンプトの最初の指示文の後に挿入
    if "してください。" in prompt:
        parts = prompt.split("してください。", 1)
        if len(parts) == 2:
            return parts[0] + "してください。" + rag_section + parts[1]

    # デフォルトでは先頭に追加
    return rag_section + prompt
