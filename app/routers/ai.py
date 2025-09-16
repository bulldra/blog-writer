import json
import logging as _logging
import os
from typing import Any, AsyncGenerator, List, Literal, Mapping, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from google import genai as genai_client
from google.genai import types as genai_types
from pydantic import BaseModel

from app.ai_utils import (
    apply_prompt_template,
    build_bullets_prompt,
    extract_text,
    generate_rag_query,
    inject_rag_context,
)
from app.security import decrypt_text, encrypt_text, is_url_allowed
from app.storage import get_ai_settings, save_ai_settings

router = APIRouter()

ALLOWED_MODELS = {"gemini-2.5-pro", "gemini-2.5-flash"}
LEGACY_MODEL_MAP = {
    "gemini-1.5-flash": "gemini-2.5-flash",
    "gemini-1.5-pro": "gemini-2.5-pro",
}

MAX_PROMPT_LEN = 32768
_logger = _logging.getLogger(__name__)


class SettingsUpdate(BaseModel):
    provider: Literal["gemini", "lmstudio"] = "gemini"
    api_key: str
    model: str = "gemini-2.5-flash"
    max_prompt_len: Optional[int] = None


class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    url_context: Optional[str] = None
    highlights: Optional[List[str]] = None
    enable_rag: bool = False
    rag_book_name: Optional[str] = None
    title: Optional[str] = None


@router.get("/settings")
def get_settings():
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    default_model = (
        "openai/gpt-oss-20b" if provider == "lmstudio" else "gemini-2.5-flash"
    )
    model = str(row.get("model", default_model))
    if provider == "gemini":
        model = LEGACY_MODEL_MAP.get(model, model)
    return {
        "provider": provider,
        "model": model,
        "hasKey": bool(row.get("api_key")),
        "max_prompt_len": int(row.get("max_prompt_len", 32768)),
    }


@router.post("/settings")
def save_settings(payload: SettingsUpdate):
    provider = payload.provider
    app_secret = os.getenv("APP_SECRET")
    if provider == "gemini":
        model = LEGACY_MODEL_MAP.get(payload.model, payload.model)
        if model not in ALLOWED_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"model must be one of {sorted(ALLOWED_MODELS)}",
            )
        enc = encrypt_text(payload.api_key or "", app_secret)
        save_ai_settings(provider, model, enc, max_prompt_len=payload.max_prompt_len)
        return {"ok": True}
    if provider == "lmstudio":
        model = payload.model or "openai/gpt-oss-20b"
        base = payload.api_key.strip() or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        enc = encrypt_text(base, app_secret)
        save_ai_settings(provider, model, enc, max_prompt_len=payload.max_prompt_len)
        return {"ok": True}
    raise HTTPException(status_code=400, detail="unsupported provider")


def _build_tools(enable_search: bool = True, enable_url: bool = True) -> list:
    tools: list = []
    if enable_search:
        try:
            tools.append(genai_types.Tool(google_search=genai_types.GoogleSearch()))
        except Exception:
            pass
    if enable_url:
        try:
            tools.append(genai_types.Tool(url_context=genai_types.UrlContext()))
        except Exception:
            pass
    return tools


def _url_part(url: str) -> object:
    """Create a URL content part for url-context tool without tripping mypy.

    Uses getattr to avoid attr-defined errors in type checkers while preserving
    runtime behavior with google-genai SDK.
    """
    try:
        Url: Any = getattr(genai_types, "Url")
        return Url(url=url)
    except Exception:
        return url


async def _fetch_url_context(url: str) -> Tuple[Optional[str], Optional[str]]:
    """安全なURLだけを許可して本文テキストを返すSSRf対策付きフェッチ。

    戻り値は (text, error) で、成功時は (text, None)。
    失敗時は (None, エラー種別名)。
    """
    if not is_url_allowed(url):
        return None, "url_not_allowed"
    try:
        timeout = httpx.Timeout(8.0, connect=4.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "App/1.0"})
            r.raise_for_status()
            ctype = r.headers.get("content-type", "").lower()
            if "text/html" in ctype or "text/plain" in ctype or not ctype:
                # サイズ上限を設ける
                body = r.text[: 2048 * 1024]
                text = extract_text(body)
                return text, None
            return None, "unsupported_content_type"
    except httpx.HTTPError:
        return None, "HTTPError"
    except httpx.RequestError:
        return None, "RequestError"
    except Exception:
        return None, "UnknownError"


@router.post("/generate")
@router.post("/generate")
async def generate(req: GenerateRequest):
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    model_name = req.model or str(row.get("model", "gemini-2.5-flash"))
    max_len = int(row.get("max_prompt_len", 32768))
    app_secret = os.getenv("APP_SECRET")

    # RAG検索の実行（プロンプト生成前）
    rag_context = ""
    if req.enable_rag:
        try:
            from app.routers.epub import get_rag_manager

            rag_manager = get_rag_manager()

            # 検索クエリを生成
            search_query = generate_rag_query(req.prompt, req.title)
            _logger.info(f"RAG検索クエリ: {search_query}")

            if search_query.strip():
                if req.rag_book_name:
                    # 特定の書籍で検索
                    results = rag_manager.search_in_book(
                        req.rag_book_name, search_query, 5, 0.1
                    )
                    rag_context = rag_manager.format_search_results(results)
                else:
                    # 全書籍で検索
                    all_results = rag_manager.search_all_books(search_query, 3, 0.1)
                    # 結果を統合
                    combined_results = []
                    for book_results in all_results.values():
                        combined_results.extend(book_results)
                    # スコア順でソートして上位5件
                    combined_results.sort(key=lambda x: x[2], reverse=True)
                    rag_context = rag_manager.format_search_results(
                        combined_results[:5]
                    )

                _logger.info(f"RAG検索結果取得: {len(rag_context)}文字")
        except Exception as e:
            _logger.warning(f"RAG検索エラー: {e}")
            rag_context = ""

    # プロンプトの基本処理
    base_prompt = (req.prompt or "")[:max_len]

    # RAGコンテキストを注入
    if rag_context:
        base_prompt = inject_rag_context(base_prompt, rag_context)

    # LM Studio: OpenAI互換API（/v1/chat/completions）
    if provider == "lmstudio":
        base = decrypt_text(str(row.get("api_key", "")), app_secret) or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        url = (base.rstrip("/")) + "/chat/completions"
        prompt = base_prompt
        if req.url_context:
            ctx, err = await _fetch_url_context(req.url_context)
            if ctx:
                prompt = (
                    "次のURL本文を参考に回答してください。まず要点を整理し、続いて求められた出力を生成してください。\n"
                    f"URL: {req.url_context}\n\n[URL本文]\n{ctx}\n\n[依頼]\n{prompt}"
                )
            elif err:
                prompt = (
                    "次のURLの内容を参考にしつつ回答してください。本文取得に失敗した場合は一般知識で補ってください。\n"
                    f"URL: {req.url_context}\n\n{prompt}"
                )
        if req.highlights:
            hlines = [f"- {h.strip()}" for h in req.highlights if h and h.strip()]
            htext = "\n".join(hlines[:300])[:4000]
            if htext:
                prompt = f"{prompt}\n\n[参考引用]\n{htext}\n"
        try:
            async with httpx.AsyncClient(timeout=60.0) as http:
                r = await http.post(
                    url,
                    json={
                        "model": model_name or "openai/gpt-oss-20b",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                    },
                )
                r.raise_for_status()
                data = r.json()
                txt = (
                    (data.get("choices") or [{}])[0].get("message", {}).get("content")
                ) or ((data.get("choices") or [{}])[0].get("text"))
                return {"text": str(txt or "")}
        except Exception as e:
            _logger.warning("lmstudio.generate failed: %r", e)
            return {"text": f"[stub-lmstudio] {prompt}"}

    # Gemini 既存経路
    stored = row.get("api_key") or os.getenv("GEMINI_API_KEY")
    api_key = decrypt_text(str(stored or ""), app_secret)
    if model_name not in ALLOWED_MODELS:
        model_name = "gemini-2.5-flash"
    if not api_key:
        return {"text": f"[stub] {base_prompt}"}
    prompt = base_prompt
    try:
        gclient = genai_client.Client(api_key=api_key)
        tools = _build_tools(enable_search=True, enable_url=bool(req.url_context))
        config = genai_types.GenerateContentConfig(tools=tools)
        contents: list = []
        if req.url_context:
            contents.append(_url_part(req.url_context))
        body = prompt
        if req.highlights:
            hlines = [f"- {h.strip()}" for h in req.highlights if h and h.strip()]
            htext = "\n".join(hlines[:300])[:4000]
            if htext:
                body = f"{body}\n\n[参考引用]\n{htext}\n"
        contents.append(body)
        resp2 = gclient.models.generate_content(
            model=model_name, contents=contents, config=config
        )
        text = getattr(resp2, "text", None) or ""
        if text:
            return {"text": text}
    except Exception:
        pass
    if req.url_context:
        ctx, err = await _fetch_url_context(req.url_context)
        if ctx:
            prompt = (
                "次のURL本文を参考に回答してください。まず要点を整理し、続いて求められた出力を生成してください。\n"
                f"URL: {req.url_context}\n\n"
                f"[URL本文]\n{ctx}\n\n[依頼]\n{base_prompt}"
            )
        elif err:
            prompt = (
                "次のURLの内容を参考にしつつ回答してください。本文取得に失敗した場合は一般知識で補ってください。\n"
                f"URL: {req.url_context}\n\n{base_prompt}"
            )
    gclient = genai_client.Client(api_key=api_key)
    resp3 = gclient.models.generate_content(model=model_name, contents=prompt[:max_len])
    return {"text": getattr(resp3, "text", None) or ""}


class BulletsRequest(BaseModel):
    bullets: List[str]
    title: Optional[str] = None
    style: Optional[str] = None
    length: Optional[str] = None
    enforce_headings: Optional[bool] = None
    model: Optional[str] = None
    url_context: Optional[str] = None
    highlights: Optional[List[str]] = None
    highlights_asin: Optional[List[Optional[str]]] = None
    prompt_template: Optional[str] = None
    article_type: Optional[Literal["url", "note", "review"]] = None
    extra_context: Optional[Mapping[str, str]] = None


_apply_prompt_template = apply_prompt_template


def _build_bullets_prompt(
    req: BulletsRequest, bullets: List[str]
) -> str:  # legacy wrapper
    return build_bullets_prompt(req, bullets)


def _sanitize_bullets_request(req: BulletsRequest) -> BulletsRequest:
    at = (req.article_type or "").strip()
    if at == "note":
        return req.model_copy(
            update={"url_context": None, "highlights": None, "highlights_asin": None}
        )
    if at == "url":
        return req.model_copy(update={"highlights": None, "highlights_asin": None})
    if at == "review":
        return req.model_copy(update={"url_context": None})
    return req


@router.post("/from-bullets")
async def from_bullets(req: BulletsRequest):
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    app_secret = os.getenv("APP_SECRET")
    model_name = req.model or str(row.get("model", "gemini-2.5-flash"))
    max_len = int(row.get("max_prompt_len", 32768))

    req2 = _sanitize_bullets_request(req)
    bullets = [b.strip() for b in (req2.bullets or []) if b and b.strip()]
    prompt = _build_bullets_prompt(req2, bullets)

    if provider == "lmstudio":
        base = decrypt_text(str(row.get("api_key", "")), app_secret) or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        url = (base.rstrip("/")) + "/chat/completions"
        if req2.url_context:
            ctx, err = await _fetch_url_context(req2.url_context)
            if ctx:
                prompt = (
                    prompt + "\n[参考URL本文] 以下の内容も参考にしてください。\n" + ctx
                )
            elif err:
                prompt = (
                    prompt
                    + "\n[参考URL] 指定URLの本文取得に失敗したため、一般知識で補ってください。\n"
                )
        try:
            async with httpx.AsyncClient(timeout=60.0) as http:
                r = await http.post(
                    url,
                    json={
                        "model": model_name or "openai/gpt-oss-20b",
                        "messages": [{"role": "user", "content": prompt[:max_len]}],
                        "temperature": 0.7,
                    },
                )
                r.raise_for_status()
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                message = choice.get("message", {})
                reasoning = message.get("reasoning_content") or choice.get(
                    "reasoning_content"
                )
                content = message.get("content") or choice.get("text")
                if reasoning:
                    out = f"[Reasoning]\n{reasoning}\n\n---\n\n[生成結果]\n{content or ''}"
                else:
                    out = content or ""
                return {"text": str(out)}
        except Exception as e:
            _logger.warning("lmstudio.from_bullets failed: %r", e)
            return {"text": _build_stub_text_from_bullets(bullets)}

    # Gemini
    stored = row.get("api_key") or os.getenv("GEMINI_API_KEY")
    api_key = decrypt_text(str(stored or ""), app_secret)
    if model_name not in ALLOWED_MODELS:
        model_name = "gemini-2.5-flash"
    if not api_key:
        return {"text": _build_stub_text_from_bullets(bullets)}
    try:
        gclient = genai_client.Client(api_key=api_key)
        tools = _build_tools(enable_search=True, enable_url=bool(req2.url_context))
        config = genai_types.GenerateContentConfig(tools=tools)
        contents: list = []
        if req2.url_context:
            contents.append(_url_part(req2.url_context))
        contents.append(prompt[:max_len])
        resp2 = gclient.models.generate_content(
            model=model_name, contents=contents, config=config
        )
        text = getattr(resp2, "text", None) or ""
        if text:
            return {"text": text}
    except Exception:
        pass
    if req2.url_context:
        ctx, err = await _fetch_url_context(req2.url_context)
        if ctx:
            prompt = prompt + "\n[参考URL本文] 以下の内容も参考にしてください。\n" + ctx
        elif err:
            prompt = (
                prompt
                + "\n[参考URL] 指定URLの本文取得に失敗したため、一般知識で補ってください。\n"
            )
    gclient = genai_client.Client(api_key=api_key)
    resp3 = gclient.models.generate_content(model=model_name, contents=prompt[:max_len])
    return {"text": getattr(resp3, "text", None) or ""}


async def _chunk_text(text: str, size: int = 600) -> AsyncGenerator[bytes, None]:
    for i in range(0, len(text), size):
        yield text[i : i + size].encode("utf-8", errors="ignore")


def _build_stub_text_from_bullets(bullets: List[str]) -> str:
    lines: List[str] = [
        "[Reasoning]",
        "- 箇条書きから記事の骨子を組み立てます。",
        "- 導入→背景→要点→考察→結論の順に配置します。",
    ]
    if bullets:
        preview = ", ".join([b for b in bullets[:10]])
        lines.append(f"- 重要語句: {preview}")
    else:
        lines.append("- 箇条書きは空なので、一般的な構成で下書きを作成します。")
    lines.append("\n---\n")
    outline = [
        "[生成結果]",
        "# タイトル案",
        "",
        "## 導入",
        "話題の背景と狙いを簡潔に述べます。",
        "",
        "## 本文",
        "要点を段落に分けて展開します。",
        "",
        "## まとめ",
        "得られた気づきと今後のアクションを提示します。",
    ]
    return "\n".join(lines + outline)


# _stream_stub_from_bullets: 不要になったため削除（Reasoning は LLM 出力に統一）


@router.post("/from-bullets/stream")
async def from_bullets_stream(req: BulletsRequest):
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    app_secret = os.getenv("APP_SECRET")
    model_name = req.model or str(row.get("model", "gemini-2.5-flash"))
    max_len = int(row.get("max_prompt_len", 32768))

    req2 = _sanitize_bullets_request(req)
    bullets = [b.strip() for b in (req2.bullets or []) if b and b.strip()]
    prompt = _build_bullets_prompt(req2, bullets)

    if provider == "lmstudio":
        base = decrypt_text(str(row.get("api_key", "")), app_secret) or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        url = (base.rstrip("/")) + "/chat/completions"

        async def _lm_stream():
            _p = prompt
            if req2.url_context:
                ctx, err = await _fetch_url_context(req2.url_context)
                if ctx:
                    _p = _p + "\n[参考URL本文] 以下の内容も参考にしてください。\n" + ctx
                elif err:
                    _p = (
                        _p
                        + "\n[参考URL] 指定URLの本文取得に失敗したため、一般知識で補ってください。\n"
                    )
            # LM Studio: モデルの reasoning_content を優先して利用する
            try:
                async with httpx.AsyncClient(timeout=None) as http:
                    # OpenAI互換 SSE ストリーム
                    async with http.stream(
                        "POST",
                        url,
                        json={
                            "model": model_name or "openai/gpt-oss-20b",
                            "messages": [{"role": "user", "content": _p[:max_len]}],
                            "temperature": 0.7,
                            "stream": True,
                        },
                        timeout=120.0,
                    ) as r:
                        r.raise_for_status()
                        sent_reasoning = False
                        sent_result_header = False
                        async for line in r.aiter_lines():
                            if not line:
                                continue
                            # 期待形式:  "data: {json}"
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    obj = json.loads(data_str)
                                except Exception:
                                    continue
                                choice = (obj.get("choices") or [{}])[0]
                                # chat.completions: delta.content
                                delta_obj = choice.get("delta") or {}
                                # reasoning_content または reasoning（実装差対応）
                                rchunk = (
                                    delta_obj.get("reasoning_content")
                                    or choice.get("reasoning_content")
                                    or delta_obj.get("reasoning")
                                )
                                tchunk = delta_obj.get("content") or choice.get("text")
                                if rchunk:
                                    if not sent_reasoning:
                                        yield "[Reasoning]\n".encode(
                                            "utf-8", errors="ignore"
                                        )
                                        sent_reasoning = True
                                    yield str(rchunk).encode("utf-8", errors="ignore")
                                if tchunk:
                                    if sent_reasoning and not sent_result_header:
                                        yield "\n\n---\n\n[生成結果]\n".encode(
                                            "utf-8", errors="ignore"
                                        )
                                        sent_result_header = True
                                    if not sent_reasoning and not sent_result_header:
                                        # reasoning が無い場合でも UI 互換のため見出しを出す
                                        yield "[生成結果]\n".encode(
                                            "utf-8", errors="ignore"
                                        )
                                        sent_result_header = True
                                    yield str(tchunk).encode("utf-8", errors="ignore")
            except Exception as e:
                _logger.warning("lmstudio.stream failed: %r", e)
                stub_text = _build_stub_text_from_bullets(bullets)
                async for chunk in _chunk_text(stub_text):
                    yield chunk
            return

        return StreamingResponse(
            _lm_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Accel-Buffering": "no",
            },
        )

    # Gemini 既存経路
    stored = row.get("api_key") or os.getenv("GEMINI_API_KEY")
    api_key = decrypt_text(str(stored or ""), app_secret)
    if model_name not in ALLOWED_MODELS:
        model_name = "gemini-2.5-flash"

    if not api_key:

        async def _stub_stream():
            stub = _build_stub_text_from_bullets(bullets)
            async for chunk in _chunk_text(stub):
                yield chunk

        return StreamingResponse(
            _stub_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Accel-Buffering": "no",
            },
        )

    async def _gen_stream():
        # 最終プロンプトを先に構築（Reasoning にも使用）
        if req2.url_context:
            ctx, err = await _fetch_url_context(req2.url_context)
            if ctx:
                _p = prompt + "\n[参考URL本文] 以下の内容も参考にしてください。\n" + ctx
            elif err:
                _p = (
                    prompt
                    + "\n[参考URL] 指定URLの本文取得に失敗したため、一般知識で補ってください。\n"
                )
            else:
                _p = prompt
        else:
            _p = prompt

        # Reasoning/生成結果のセクションを LLM に出力させる指示を先頭に付与
        format_inst = (
            "出力フォーマット: 以下の2セクション構成で必ず出力してください。\n"
            "[Reasoning]\n"
            "この記事を作る意図・観点の要約（箇条書き3-6項目）。内的手順や機密は書かない。\n"
            "---\n"
            "[生成結果]\n"
            "最終的なMarkdown本文（# 見出しを含む）。\n"
        )
        _p = format_inst + "\n" + _p

        try:
            gclient = genai_client.Client(api_key=api_key)
            # 従来どおり tools + prompt を使用しつつ、Reasoning には _p を表示
            tools = _build_tools(enable_search=True, enable_url=bool(req2.url_context))
            config = genai_types.GenerateContentConfig(tools=tools)
            contents: list = []
            if req2.url_context:
                contents.append(_url_part(req2.url_context))
            contents.append(_p[:max_len])
            resp2 = gclient.models.generate_content(
                model=model_name, contents=contents, config=config
            )
            text = getattr(resp2, "text", None) or ""
            async for chunk in _chunk_text(text):
                yield chunk
            return
        except Exception:
            pass

        # フォールバック: _p を直接コンテンツとして送る
        gclient = genai_client.Client(api_key=api_key)
        resp3 = gclient.models.generate_content(model=model_name, contents=_p[:max_len])
        text = getattr(resp3, "text", None) or ""
        async for chunk in _chunk_text(text):
            yield chunk
        return

    return StreamingResponse(
        _gen_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/from-bullets/prompt")
async def from_bullets_prompt(req: BulletsRequest):
    """最終的に使用するプロンプトを返す。モデル呼び出しは行わない。"""
    req2 = _sanitize_bullets_request(req)
    bullets = [b.strip() for b in (req2.bullets or []) if b and b.strip()]
    prompt = _build_bullets_prompt(req2, bullets)
    if req2.url_context:
        ctx, err = await _fetch_url_context(req2.url_context)
        if ctx:
            prompt = prompt + "\n[参考URL本文]\n" + ctx
        elif err:
            prompt = (
                prompt
                + "\n[参考URL] 指定URLの本文取得に失敗したため、一般知識で補ってください。\n"
            )
    row = get_ai_settings()
    max_len = int(row.get("max_prompt_len", 32768))
    return {"prompt": prompt[:max_len]}


class EditRequest(BaseModel):
    content: str
    instruction: str
    model: Optional[str] = None


@router.post("/edit")
async def edit_content(req: EditRequest):
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    app_secret = os.getenv("APP_SECRET")
    model_name = req.model or str(row.get("model", "gemini-2.5-flash"))
    max_len = int(row.get("max_prompt_len", 32768))
    if provider == "gemini" and model_name not in ALLOWED_MODELS:
        model_name = "gemini-2.5-flash"

    content = (req.content or "").strip()
    instruction = (req.instruction or "").strip()
    if not content or not instruction:
        raise HTTPException(status_code=400, detail="content/instruction required")

    prompt = (
        "次のMarkdown文章を、与えられた指示に厳密に従って推敲・編集してください。\n"
        "- 出力はMarkdown形式のみ。余計な前置きや説明は書かない。\n"
        "- 文章構成は保ちつつ、必要に応じて改善して良い。\n\n"
        f"[指示]\n{instruction}\n\n[文章]\n{content}\n"
    )

    if provider == "lmstudio":
        base = decrypt_text(str(row.get("api_key", "")), app_secret) or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        url = (base.rstrip("/")) + "/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    url,
                    json={
                        "model": model_name or "openai/gpt-oss-20b",
                        "messages": [{"role": "user", "content": prompt[:max_len]}],
                        "temperature": 0.3,
                    },
                )
                r.raise_for_status()
                data = r.json()
                txt = (
                    (data.get("choices") or [{}])[0].get("message", {}).get("content")
                ) or ((data.get("choices") or [{}])[0].get("text"))
                return {"text": str(txt or content)}
        except Exception as e:
            _logger.warning("lmstudio.edit failed: %r", e)
            return {"text": content + "\n\n[stub-edit] " + instruction}

    stored = row.get("api_key") or os.getenv("GEMINI_API_KEY")
    api_key = decrypt_text(str(stored or ""), app_secret)
    if not api_key:
        return {"text": content + "\n\n[stub-edit] " + instruction}
    gclient = genai_client.Client(api_key=api_key)
    resp = gclient.models.generate_content(model=model_name, contents=prompt[:max_len])
    return {"text": getattr(resp, "text", None) or content}


# 編集ストリーミングAPI
@router.post("/edit/stream")
async def edit_content_stream(req: EditRequest):
    row = get_ai_settings()
    provider = str(row.get("provider", "gemini"))
    app_secret = os.getenv("APP_SECRET")
    model_name = req.model or str(row.get("model", "gemini-2.5-flash"))
    max_len = int(row.get("max_prompt_len", 32768))
    if provider == "gemini" and model_name not in ALLOWED_MODELS:
        model_name = "gemini-2.5-flash"

    content = (req.content or "").strip()
    instruction = (req.instruction or "").strip()
    if not content or not instruction:
        raise HTTPException(status_code=400, detail="content/instruction required")

    prompt = (
        "次のMarkdown文章を、与えられた指示に厳密に従って推敲・編集してください。\n"
        "- 出力はMarkdown形式のみ。余計な前置きや説明は書かない。\n"
        "- 文章構成は保ちつつ、必要に応じて改善して良い。\n\n"
        f"[指示]\n{instruction}\n\n[文章]\n{content}\n"
    )

    if provider == "lmstudio":
        base = decrypt_text(str(row.get("api_key", "")), app_secret) or os.getenv(
            "LMSTUDIO_BASE", "http://localhost:1234/v1"
        )
        url = (base.rstrip("/")) + "/chat/completions"

        async def _lm_stream():
            try:
                async with httpx.AsyncClient(timeout=None) as http:
                    async with http.stream(
                        "POST",
                        url,
                        json={
                            "model": model_name or "openai/gpt-oss-20b",
                            "messages": [{"role": "user", "content": prompt[:max_len]}],
                            "temperature": 0.3,
                            "stream": True,
                        },
                        timeout=120.0,
                    ) as r:
                        r.raise_for_status()
                        async for line in r.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    obj = json.loads(data_str)
                                except Exception:
                                    continue
                                choice = (obj.get("choices") or [{}])[0]
                                delta_obj = choice.get("delta") or {}
                                tchunk = delta_obj.get("content") or choice.get("text")
                                if tchunk:
                                    yield str(tchunk).encode("utf-8", errors="ignore")
            except Exception as e:
                _logger.warning("lmstudio.edit.stream failed: %r", e)
                stub_text = content + "\n\n[stub-edit] " + instruction
                async for chunk in _chunk_text(stub_text):
                    yield chunk
            return

        return StreamingResponse(
            _lm_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Accel-Buffering": "no",
            },
        )

    stored = row.get("api_key") or os.getenv("GEMINI_API_KEY")
    api_key = decrypt_text(str(stored or ""), app_secret)
    if not api_key:

        async def _stub_stream():
            stub = content + "\n\n[stub-edit] " + instruction
            async for chunk in _chunk_text(stub):
                yield chunk

        return StreamingResponse(
            _stub_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Accel-Buffering": "no",
            },
        )

    async def _gen_stream():
        try:
            gclient = genai_client.Client(api_key=api_key)
            config = genai_types.GenerateContentConfig()
            resp2 = gclient.models.generate_content(
                model=model_name, contents=prompt[:max_len], config=config
            )
            text = getattr(resp2, "text", None) or ""
            async for chunk in _chunk_text(text):
                yield chunk
            return
        except Exception:
            pass
        gclient = genai_client.Client(api_key=api_key)
        resp3 = gclient.models.generate_content(
            model=model_name, contents=prompt[:max_len]
        )
        text = getattr(resp3, "text", None) or ""
        async for chunk in _chunk_text(text):
            yield chunk
        return

    return StreamingResponse(
        _gen_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",
        },
    )


_logging.getLogger(__name__).info(
    "ai.routes=%s", [getattr(r, "path", "?") for r in router.routes]
)
