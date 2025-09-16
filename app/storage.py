import json
import os
import re
import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(os.getenv("BLOGWRITER_DATA_DIR", "./data")).resolve()
SETTINGS_FILE = DATA_DIR / "settings.json"
DRAFTS_FILE = DATA_DIR / "drafts.json"
PHRASES_FILE = DATA_DIR / "phrases.json"
GENERATION_HISTORY_FILE = DATA_DIR / "generation_history.json"
POSTS_DIR = DATA_DIR / "posts"
EPUB_CACHE_DIR = DATA_DIR / "epub_cache"

_lock = threading.Lock()


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _atomic_write(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def init_storage() -> None:
    _ensure_dir()
    with _lock:
        if not SETTINGS_FILE.exists():
            _atomic_write(
                SETTINGS_FILE,
                {
                    "provider": "lmstudio",
                    "model": "openai/gpt-oss-20b",
                    "api_key": "",
                    "max_prompt_len": 32768,
                },
            )
        if not DRAFTS_FILE.exists():
            _atomic_write(DRAFTS_FILE, {"next_id": 1, "items": []})
        if not PHRASES_FILE.exists():
            _atomic_write(PHRASES_FILE, {"next_id": 1, "items": []})
        if not GENERATION_HISTORY_FILE.exists():
            _atomic_write(GENERATION_HISTORY_FILE, {"next_id": 1, "items": []})
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    EPUB_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_ai_settings() -> Dict[str, Any]:
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {
                "provider": "lmstudio",
                "model": "openai/gpt-oss-20b",
                "api_key": "",
                "max_prompt_len": 32768,
            },
        )
        assert isinstance(data, dict)
    maxlen = data.get("max_prompt_len", 32768)
    try:
        maxlen_i = int(maxlen)
    except Exception:
        maxlen_i = 32768
    maxlen_i = max(100, min(131072, maxlen_i))
    return {
        "provider": str(data.get("provider", "lmstudio")),
        "model": str(data.get("model", "openai/gpt-oss-20b")),
        "api_key": str(data.get("api_key", "")),
        "max_prompt_len": maxlen_i,
    }


def save_ai_settings(
    provider: str, model: str, api_key: str, *, max_prompt_len: Optional[int] = None
) -> None:
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {
                "provider": "lmstudio",
                "model": "openai/gpt-oss-20b",
                "api_key": "",
                "max_prompt_len": 32768,
            },
        )
        if not isinstance(data, dict):
            data = {}
        data["provider"] = provider
        data["model"] = model
        data["api_key"] = api_key
        if max_prompt_len is not None:
            try:
                m = int(max_prompt_len)
                m = max(100, min(131072, m))
            except Exception:
                m = 32768
            data["max_prompt_len"] = m
        _atomic_write(SETTINGS_FILE, data)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def list_drafts() -> List[Dict[str, Any]]:
    with _lock:
        data = _read_json(DRAFTS_FILE, {"next_id": 1, "items": []})
        items = data.get("items", [])
        assert isinstance(items, list)
        return sorted(
            [
                {
                    "id": int(it["id"]),
                    "title": str(it.get("title", "")),
                    "content": str(it.get("content", "")),
                    "created_at": str(it.get("created_at", _now_iso())),
                    "updated_at": str(it.get("updated_at", _now_iso())),
                }
                for it in items
            ],
            key=lambda d: (d["updated_at"], d["id"]),
            reverse=True,
        )


def create_draft(title: str, content: str) -> Dict[str, Any]:
    with _lock:
        data = _read_json(DRAFTS_FILE, {"next_id": 1, "items": []})
        next_id = int(data.get("next_id", 1))
        now = _now_iso()
        row = {
            "id": next_id,
            "title": title or "無題",
            "content": content,
            "created_at": now,
            "updated_at": now,
        }
        items = list(data.get("items", []))
        items.append(row)
        _atomic_write(DRAFTS_FILE, {"next_id": next_id + 1, "items": items})
        return row


def get_draft(draft_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        data = _read_json(DRAFTS_FILE, {"next_id": 1, "items": []})
        for it in data.get("items", []):
            if int(it.get("id")) == draft_id:
                return {
                    "id": int(it["id"]),
                    "title": str(it.get("title", "")),
                    "content": str(it.get("content", "")),
                    "created_at": str(it.get("created_at", _now_iso())),
                    "updated_at": str(it.get("updated_at", _now_iso())),
                }
        return None


def update_draft(
    draft_id: int, title: Optional[str], content: Optional[str]
) -> Optional[Dict[str, Any]]:
    with _lock:
        data = _read_json(DRAFTS_FILE, {"next_id": 1, "items": []})
        changed = False
        for it in data.get("items", []):
            if int(it.get("id")) == draft_id:
                if title is not None and title.strip():
                    it["title"] = title.strip()
                    changed = True
                if content is not None:
                    it["content"] = content
                    changed = True
                if changed:
                    it["updated_at"] = _now_iso()
                row = {
                    "id": int(it["id"]),
                    "title": str(it.get("title", "")),
                    "content": str(it.get("content", "")),
                    "created_at": str(it.get("created_at", _now_iso())),
                    "updated_at": str(it.get("updated_at", _now_iso())),
                }
                _atomic_write(DRAFTS_FILE, data)
                return row
        return None


def delete_draft(draft_id: int) -> bool:
    with _lock:
        data = _read_json(DRAFTS_FILE, {"next_id": 1, "items": []})
        items = list(data.get("items", []))
        new_items = [it for it in items if int(it.get("id")) != draft_id]
        if len(new_items) == len(items):
            return False
        data["items"] = new_items
        _atomic_write(DRAFTS_FILE, data)
        return True


# ===== Phrases =====
def list_phrases() -> List[Dict[str, Any]]:
    with _lock:
        data = _read_json(PHRASES_FILE, {"next_id": 1, "items": []})
        items = data.get("items", [])
        assert isinstance(items, list)
        return sorted(
            [
                {
                    "id": int(it["id"]),
                    "text": str(it.get("text", "")),
                    "note": (str(it["note"]) if it.get("note") is not None else None),
                    "created_at": str(it.get("created_at", _now_iso())),
                    "updated_at": str(it.get("updated_at", _now_iso())),
                }
                for it in items
            ],
            key=lambda d: (d["updated_at"], d["id"]),
            reverse=True,
        )


def create_phrase(text: str, note: Optional[str] = None) -> Dict[str, Any]:
    with _lock:
        data = _read_json(PHRASES_FILE, {"next_id": 1, "items": []})
        next_id = int(data.get("next_id", 1))
        now = _now_iso()
        row = {
            "id": next_id,
            "text": text,
            "note": note,
            "created_at": now,
            "updated_at": now,
        }
        items = list(data.get("items", []))
        items.append(row)
        _atomic_write(PHRASES_FILE, {"next_id": next_id + 1, "items": items})
        return row


def delete_phrase(phrase_id: int) -> bool:
    with _lock:
        data = _read_json(PHRASES_FILE, {"next_id": 1, "items": []})
        items = list(data.get("items", []))
        new_items = [it for it in items if int(it.get("id")) != phrase_id]
        if len(new_items) == len(items):
            return False
        data["items"] = new_items
        _atomic_write(PHRASES_FILE, data)
        return True


# ===== Markdown Posts =====
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")


def _guess_title_and_body(md: str) -> Tuple[Optional[str], str]:
    lines = md.splitlines()
    title: Optional[str] = None
    if lines:
        m = _TITLE_RE.match(lines[0].strip())
        if m:
            title = m.group(1).strip()
    return title, md


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s\-]+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def save_markdown_post(content: str, git_commit: bool = False) -> Dict[str, Any]:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    title, body = _guess_title_and_body(content)
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    base = _slugify(title or "untitled")
    filename = f"{ts}-{base}.md"
    path = POSTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        f.write(body)
        if not body.endswith("\n"):
            f.write("\n")
    if git_commit:
        # best-effort; git が無い/未初期化でも無視
        subprocess.run(["git", "add", str(path)], check=False)
        msg = f"Add post: {title or 'untitled'}"
        subprocess.run(["git", "commit", "-m", msg], check=False)
    return {"path": str(path), "title": title, "filename": filename}


def list_markdown_posts(limit: int = 50) -> List[Dict[str, Any]]:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    files = [p for p in POSTS_DIR.glob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    result: List[Dict[str, Any]] = []
    for p in files[: max(1, limit)]:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        title, _ = _guess_title_and_body(text)
        st = p.stat()
        result.append(
            {
                "filename": p.name,
                "title": title or p.stem,
                "mtime": int(st.st_mtime),
                "size": int(st.st_size),
            }
        )
    return result


def read_markdown_post(filename: str) -> Optional[str]:
    # パストラバーサル対策: 直下のファイル名のみ許可
    if "/" in filename or ".." in filename:
        return None
    path = POSTS_DIR / filename
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def delete_markdown_post(filename: str) -> bool:
    # パストラバーサル対策: 直下のファイル名のみ許可
    if "/" in filename or ".." in filename:
        return False
    path = POSTS_DIR / filename
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except OSError:
        return False


# ===== Prompt Templates (persist into settings.json) =====
def list_prompt_templates() -> List[Dict[str, str]]:
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = list(data.get("prompt_templates", []))
        rows: List[Dict[str, str]] = []
        for it in items:
            name = str(it.get("name", "")).strip()
            content = str(it.get("content", ""))
            if name:
                rows.append({"name": name, "content": content})
        # 先頭優先（直近追加を上に想定）
        return rows


def save_prompt_template(name: str, content: str) -> Dict[str, str]:
    name = name.strip()
    if not name:
        raise ValueError("template name is required")
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = list(data.get("prompt_templates", []))
        # upsert by name
        idx = next((i for i, it in enumerate(items) if str(it.get("name")) == name), -1)
        row = {"name": name, "content": content}
        if idx >= 0:
            items[idx] = row
        else:
            items.insert(0, row)
        data["prompt_templates"] = items
        _atomic_write(SETTINGS_FILE, data)
        return row


def delete_prompt_template(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = list(data.get("prompt_templates", []))
        new_items = [it for it in items if str(it.get("name")) != name]
        if len(new_items) == len(items):
            return False
        data["prompt_templates"] = new_items
        _atomic_write(SETTINGS_FILE, data)
        return True


def get_prompt_template(name: str) -> Optional[Dict[str, str]]:
    name = name.strip()
    if not name:
        return None
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = list(data.get("prompt_templates", []))
        for it in items:
            if str(it.get("name")) == name:
                return {"name": name, "content": str(it.get("content", ""))}
    return None


def cleanup_prompt_templates() -> int:
    """Remove duplicate prompt templates by name, keeping the first occurrence.

    Returns the number of removed entries.
    """
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = list(data.get("prompt_templates", []))
        seen: set[str] = set()
        new_items: List[Dict[str, str]] = []
        removed = 0
        for it in items:
            n = str(it.get("name", "")).strip()
            if not n:
                removed += 1
                continue
            if n in seen:
                removed += 1
                continue
            seen.add(n)
            new_items.append({"name": n, "content": str(it.get("content", ""))})
        if removed:
            data["prompt_templates"] = new_items
            _atomic_write(SETTINGS_FILE, data)
        return removed


# ===== Article Templates (persist into settings.json) =====
_BUILTIN_ARTICLE_TYPES = {"url", "note", "review"}

# ウィジェットタイプの定義
WIDGET_TYPES = {
    "properties": {
        "id": "properties",
        "name": "プロパティセット",
        "description": "記事のメタデータやカスタムフィールドを設定します",
    },
    "url_context": {
        "id": "url_context",
        "name": "URL コンテキスト",
        "description": "指定したURLの内容を取得して記事作成の参考にします",
    },
    "kindle": {
        "id": "kindle",
        "name": "Kindle ハイライト",
        "description": "Obsidianから取得したKindleハイライトを記事作成の参考にします",
    },
    "past_posts": {
        "id": "past_posts",
        "name": "過去記事",
        "description": "過去に書いた記事の内容を参考にして記事を作成します",
    },
    "epub": {
        "id": "epub",
        "name": "EPUB書籍検索",
        "description": "EPUBファイルからベクトル検索でRAG機能を提供し、書籍内容を記事作成の参考にします",
    },
    "notion": {
        "id": "notion",
        "name": "Notion連携",
        "description": "NotionのページやデータベースからMCP経由で情報を取得し、記事作成の参考にします",
    },
}

_ALLOWED_WIDGETS = set(WIDGET_TYPES.keys())


def _default_article_templates() -> Dict[str, Any]:
    return {
        "url": {
            "type": "url",
            "name": "URL コンテキスト",
            "fields": [
                {"key": "goal", "label": "目的", "input_type": "text"},
                {"key": "audience", "label": "読者", "input_type": "text"},
                {"key": "tone", "label": "トーン/スタイル", "input_type": "text"},
                {"key": "url", "label": "参照するURL", "input_type": "text"},
            ],
            "prompt_template": "",
            "widgets": ["url_context"],
        },
        "note": {
            "type": "note",
            "name": "雑記",
            "fields": [
                {"key": "theme", "label": "テーマ", "input_type": "text"},
                {"key": "goal", "label": "目的", "input_type": "text"},
                {"key": "audience", "label": "読者", "input_type": "text"},
                {"key": "tone", "label": "トーン/スタイル", "input_type": "text"},
            ],
            "prompt_template": "",
            "widgets": [],
        },
        "review": {
            "type": "review",
            "name": "書評",
            "fields": [
                {"key": "book_title", "label": "書籍タイトル", "input_type": "text"},
                {"key": "book_author", "label": "著者", "input_type": "text"},
                {"key": "impressions", "label": "所感/要旨", "input_type": "textarea"},
                {"key": "recommend", "label": "おすすめポイント", "input_type": "text"},
                {"key": "caveats", "label": "注意点", "input_type": "text"},
                {"key": "audience", "label": "対象読者", "input_type": "text"},
                {"key": "tone", "label": "トーン/スタイル", "input_type": "text"},
            ],
            "prompt_template": "",
            "widgets": ["kindle"],
        },
    }


def _read_article_templates() -> Dict[str, Any]:
    data = _read_json(
        SETTINGS_FILE,
        {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
    )
    items = data.get("article_templates")
    if not isinstance(items, dict):
        items = {}
    # default をマージ（上書きは既存優先）
    merged = _default_article_templates()
    # built-in は default を基本に、上書きがあれば差し替え
    for k, v in items.items():
        if not isinstance(v, dict):
            continue
        if k in _BUILTIN_ARTICLE_TYPES:
            merged[k] = v
    # カスタムテンプレート（任意ID）はそのまま追加
    for k, v in items.items():
        if not isinstance(v, dict):
            continue
        if k not in _BUILTIN_ARTICLE_TYPES:
            merged[k] = v
    return merged


def list_article_templates() -> List[Dict[str, Any]]:
    with _lock:
        merged = _read_article_templates()
        rows: List[Dict[str, Any]] = []
        for k, row in merged.items():
            if isinstance(row, dict):
                # type はキーに整合
                r = dict(row)
                r["type"] = k
                # widgets 正規化
                ws = r.get("widgets", [])
                if isinstance(ws, list):
                    r["widgets"] = [str(w) for w in ws if str(w) in _ALLOWED_WIDGETS]
                else:
                    r["widgets"] = []
                rows.append(r)
        # built-in を優先的に先頭に
        rows.sort(key=lambda x: (x["type"] not in ("url", "note", "review"), x["type"]))
        return rows


def get_article_template(t: str) -> Optional[Dict[str, Any]]:
    with _lock:
        merged = _read_article_templates()
        row = merged.get(t)
        if not isinstance(row, dict):
            return None
        r = dict(row)
        r["type"] = t
        ws = r.get("widgets", [])
        if isinstance(ws, list):
            r["widgets"] = [str(w) for w in ws if str(w) in _ALLOWED_WIDGETS]
        else:
            r["widgets"] = []
        return r


def save_article_template(t: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # validate payload minimally
    name = str(payload.get("name", "")).strip() or t
    fields = payload.get("fields", [])
    if not isinstance(fields, list):
        fields = []
    # too many fields
    if len(fields) > 30:
        raise ValueError("too many fields (>30)")
    norm_fields: List[Dict[str, str]] = []
    seen_keys: set[str] = set()
    for f in fields[:30]:
        if not isinstance(f, dict):
            continue
        key = str(f.get("key", "")).strip().lower()
        label = str(f.get("label", "")).strip()
        itype = str(f.get("input_type", "text")).strip().lower()
        if not key or not label:
            continue
        if not re.match(r"^[a-z0-9_\-]+$", key):
            continue
        if key in seen_keys:
            raise ValueError(f"duplicate field key: {key}")
        seen_keys.add(key)
        if itype not in {"text", "textarea"}:
            itype = "text"
        norm_fields.append({"key": key, "label": label, "input_type": itype})
    prompt_template = str(payload.get("prompt_template", ""))
    widgets_raw = payload.get("widgets", [])
    widgets: List[str] = []
    if isinstance(widgets_raw, list):
        for w in widgets_raw:
            sw = str(w)
            if sw in _ALLOWED_WIDGETS and sw not in widgets:
                widgets.append(sw)

    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = data.get("article_templates")
        if not isinstance(items, dict):
            items = {}
        row = {
            "type": t,
            "name": name,
            "fields": norm_fields,
            "prompt_template": prompt_template,
            "widgets": widgets,
        }
        items[t] = row
        data["article_templates"] = items
        _atomic_write(SETTINGS_FILE, data)
        return row


def delete_article_template(t: str) -> bool:
    with _lock:
        data = _read_json(
            SETTINGS_FILE,
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""},
        )
        items = data.get("article_templates")
        if not isinstance(items, dict):
            return True
        if t not in items:
            return True
        items = dict(items)
        items.pop(t, None)
        data["article_templates"] = items
        _atomic_write(SETTINGS_FILE, data)
        return True


def get_available_widgets() -> List[Dict[str, str]]:
    """利用可能なウィジェットタイプの一覧を取得"""
    return [
        {
            "id": widget_info["id"],
            "name": widget_info["name"],
            "description": widget_info["description"],
        }
        for widget_info in WIDGET_TYPES.values()
    ]


# ===== Generation History =====
def save_generation_history(
    title: str,
    template_type: str,
    widgets_used: List[str],
    properties: Dict[str, str],
    generated_content: str,
    reasoning: str = "",
) -> Dict[str, Any]:
    """生成履歴を保存する"""
    with _lock:
        data = _read_json(GENERATION_HISTORY_FILE, {"next_id": 1, "items": []})
        next_id = int(data.get("next_id", 1))
        now = _now_iso()

        history_item = {
            "id": next_id,
            "title": title,
            "template_type": template_type,
            "widgets_used": widgets_used,
            "properties": properties,
            "generated_content": generated_content,
            "reasoning": reasoning,
            "created_at": now,
        }

        items = list(data.get("items", []))
        items.append(history_item)

        # 最新100件まで保持
        if len(items) > 100:
            items = items[-100:]

        _atomic_write(GENERATION_HISTORY_FILE, {"next_id": next_id + 1, "items": items})
        return history_item


def list_generation_history(limit: int = 20) -> List[Dict[str, Any]]:
    """生成履歴一覧を取得する"""
    with _lock:
        data = _read_json(GENERATION_HISTORY_FILE, {"next_id": 1, "items": []})
        items = data.get("items", [])
        assert isinstance(items, list)

        result: List[Dict[str, Any]] = []
        for item in items:
            result.append(
                {
                    "id": int(item["id"]),
                    "title": str(item.get("title", "")),
                    "template_type": str(item.get("template_type", "")),
                    "widgets_used": list(item.get("widgets_used", [])),
                    "properties": dict(item.get("properties", {})),
                    "created_at": str(item.get("created_at", _now_iso())),
                    "content_length": len(str(item.get("generated_content", ""))),
                }
            )

        return sorted(result, key=lambda d: str(d["created_at"]), reverse=True)[:limit]


def get_generation_history(history_id: int) -> Optional[Dict[str, Any]]:
    """特定の生成履歴を取得する"""
    with _lock:
        data = _read_json(GENERATION_HISTORY_FILE, {"next_id": 1, "items": []})
        for item in data.get("items", []):
            if int(item.get("id")) == history_id:
                return {
                    "id": int(item["id"]),
                    "title": str(item.get("title", "")),
                    "template_type": str(item.get("template_type", "")),
                    "widgets_used": list(item.get("widgets_used", [])),
                    "properties": dict(item.get("properties", {})),
                    "generated_content": str(item.get("generated_content", "")),
                    "reasoning": str(item.get("reasoning", "")),
                    "created_at": str(item.get("created_at", _now_iso())),
                }
        return None


def delete_generation_history(history_id: int) -> bool:
    """生成履歴を削除する"""
    with _lock:
        data = _read_json(GENERATION_HISTORY_FILE, {"next_id": 1, "items": []})
        items = list(data.get("items", []))
        new_items = [item for item in items if int(item.get("id")) != history_id]
        if len(new_items) == len(items):
            return False
        data["items"] = new_items
        _atomic_write(GENERATION_HISTORY_FILE, data)
        return True


def get_notion_settings() -> Dict[str, Any]:
    """Notion MCP設定を取得する"""
    with _lock:
        data = _read_json(SETTINGS_FILE, {})
        notion_config = data.get("notion", {})
        return {
            "command": str(notion_config.get("command", "npx")),
            "args": list(notion_config.get("args", ["@modelcontextprotocol/server-notion"])),
            "env": dict(notion_config.get("env", {"NOTION_API_KEY": ""})),
            "enabled": bool(notion_config.get("enabled", False)),
            "default_parent_id": str(notion_config.get("default_parent_id", "")),
        }


def save_notion_settings(
    command: str = "npx",
    args: List[str] = None,
    env: Dict[str, str] = None,
    enabled: bool = False,
    default_parent_id: str = "",
) -> None:
    """Notion MCP設定を保存する"""
    if args is None:
        args = ["@modelcontextprotocol/server-notion"]
    if env is None:
        env = {"NOTION_API_KEY": ""}
        
    with _lock:
        data = _read_json(SETTINGS_FILE, {})
        
        notion_config = {
            "command": str(command),
            "args": list(args),
            "env": dict(env),
            "enabled": bool(enabled),
            "default_parent_id": str(default_parent_id),
        }
        
        data["notion"] = notion_config
        _atomic_write(SETTINGS_FILE, data)


def get_epub_settings() -> Dict[str, Any]:
    """EPUB設定を取得する"""
    with _lock:
        data = _read_json(SETTINGS_FILE, {})
        epub_config = data.get("epub", {})
        return {
            "epub_directory": str(epub_config.get("epub_directory", "")),
            "embedding_model": str(epub_config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")),
            "chunk_size": int(epub_config.get("chunk_size", 500)),
            "overlap_size": int(epub_config.get("overlap_size", 50)),
            "search_top_k": int(epub_config.get("search_top_k", 5)),
            "min_similarity_score": float(epub_config.get("min_similarity_score", 0.1))
        }


def save_epub_settings(
    epub_directory: str = "",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 500,
    overlap_size: int = 50,
    search_top_k: int = 5,
    min_similarity_score: float = 0.1
) -> None:
    """EPUB設定を保存する"""
    with _lock:
        data = _read_json(SETTINGS_FILE, {})
        
        epub_config = {
            "epub_directory": str(epub_directory),
            "embedding_model": str(embedding_model),
            "chunk_size": max(100, min(2000, int(chunk_size))),
            "overlap_size": max(0, min(500, int(overlap_size))),
            "search_top_k": max(1, min(20, int(search_top_k))),
            "min_similarity_score": max(0.0, min(1.0, float(min_similarity_score)))
        }
        
        data["epub"] = epub_config
        _atomic_write(SETTINGS_FILE, data)
