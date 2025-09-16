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
    notion_context: Optional[str]


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
    if req.notion_context:
        base_prompt += "\n[Notion参考情報]\n" + req.notion_context + "\n"
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
            "notion_context": req.notion_context or "",
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


async def call_ai(
    prompt: str,
) -> str:  # pragma: no cover - tests patch this  # type: ignore[no-any-return]
    """AI呼び出しの軽量スタブ。テストではこの関数をパッチする。

    Args:
        prompt: 生成に用いるプロンプト

    Returns:
        AI応答のテキスト
    """
    try:
        from app.routers.ai import GenerateRequest, generate

        req = GenerateRequest(prompt=prompt)
        resp = await generate(req)
        return str(resp.get("text", ""))
    except Exception:
        return ""


async def analyze_writing_style(text: str) -> Optional[dict]:
    """
    文章を分析して文体の特徴を抽出する

    Args:
        text: 分析対象の文章

    Returns:
        文体の特徴を表すdict、分析できない場合はNone
    """
    import json

    # 最小限の文字数チェック
    if not text or len(text.strip()) < 50:
        return None

    prompt = f"""
以下の文章を分析して、文体の特徴を抽出してください。
分析結果は以下のようなJSON形式で出力してください：

{{
    "tone": "文章の基調（例：フレンドリー、丁寧、カジュアル、フォーマル）",
    "formality": "敬語レベル（例：カジュアル、フォーマル、超フォーマル）",
    "length_preference": "文章の長さ傾向（例：簡潔、標準、詳細）",
    "target_audience": "想定読者層（例：一般、専門家、若者、ビジネス）",
    "writing_style": "文章スタイル（例：親しみやすい、説明的、論理的、感情的）",
    "sentence_structure": "文構造（例：短文中心、複文多用、バランス型）",
    "vocabulary_level": "語彙レベル（例：日常語、専門語、文語的）",
    "emotional_expression": "感情表現（例：明るく積極的、落ち着いた、熱心、冷静）"
}}

分析対象文章：
{text}

上記の文章の文体を分析し、JSON形式のみで回答してください。説明文は不要です。
"""

    try:
        result_text = await call_ai(prompt)
        if not result_text or "[stub" in result_text:
            return None

        # JSON部分を抽出
        result_text = result_text.strip()
        if result_text.startswith("{") and result_text.endswith("}"):
            pass
        elif result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()

        try:
            return json.loads(result_text)  # type: ignore[no-any-return]
        except Exception:
            import ast

            try:
                obj = ast.literal_eval(result_text)
                if isinstance(obj, dict):
                    return obj  # best-effort for dict-like strings  # type: ignore[no-any-return]
            except Exception:
                pass
            return None

    except Exception:
        return None
