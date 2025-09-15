from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, cast

logger = logging.getLogger("obsidian")

_FRONT_KEY_RE = re.compile(r"^(title|author|asin)\s*:\s*(.+?)\s*$", re.I)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
_LOC_RE = re.compile(r"(Location|位置|ページ)[\s:：]*([\d\-–]+)")
_ADDED_RE = re.compile(r"(Added on|追加)[\s:：]*([^\n]+)")


@dataclass(frozen=True)
class Highlight:
    id: str
    book: str
    text: str
    author: Optional[str] = None
    location: Optional[str] = None
    added_on: Optional[str] = None
    file: Optional[str] = None
    asin: Optional[str] = None


def _candidate_obsidian_dirs(base: Path) -> List[Path]:
    cands: List[Path] = [base / "obsidian" / "kindle_highlight"]
    logger.debug("obsidian.candidates=%s", [str(p) for p in cands])
    return cands


def _settings_path() -> Path:
    return (Path("./data") / "settings.json").resolve()


def _load_settings() -> Dict[str, object]:
    path = _settings_path()
    try:
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return cast(Dict[str, object], raw)
            logger.warning(
                "obsidian.settings_invalid_type path=%s type=%s",
                path,
                type(raw).__name__,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("obsidian.settings_read_failed path=%s err=%r", path, exc)
    return {}


def _save_settings(data: Dict[str, object]) -> None:
    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("obsidian.settings_write_failed path=%s err=%r", path, exc)


def get_configured_obsidian_dir() -> Optional[Path]:
    cfg = _load_settings()
    val = cfg.get("obsidian_dir") if isinstance(cfg, dict) else None
    if isinstance(val, str) and val.strip():
        p = Path(val).expanduser().resolve()
        if p.exists() and p.is_dir():
            return p
        logger.warning("obsidian.config_invalid path=%s", p)
    return None


def set_configured_obsidian_dir(path: Optional[str]) -> Optional[Path]:
    cfg = _load_settings()
    if not isinstance(cfg, dict):
        cfg = {}
    if path and path.strip():
        p = Path(path).expanduser().resolve()
        if not (p.exists() and p.is_dir()):
            raise OSError(f"Invalid directory: {p}")
        cfg["obsidian_dir"] = str(p)
        _save_settings(cfg)
        return p
    # クリア
    if "obsidian_dir" in cfg:
        cfg.pop("obsidian_dir", None)
        _save_settings(cfg)
    return None


def find_obsidian_dir(data_dir: Path | None = None) -> Optional[Path]:
    # 設定があれば最優先
    cfg = get_configured_obsidian_dir()
    if cfg:
        logger.info("obsidian.use_config dir=%s", cfg)
        return cfg
    base = (data_dir or Path("./data")).resolve()
    logger.info("obsidian.find base=%s", base)
    for p in _candidate_obsidian_dirs(base):
        try:
            if p.exists() and p.is_dir():
                found = p.resolve()
                logger.info("obsidian.found dir=%s", found)
                return found
        except OSError as exc:
            logger.debug("obsidian.check_error dir=%s err=%r", p, exc)
            continue
    logger.warning("obsidian.not_found base=%s", base)
    return None


def iter_md_files(root: Path) -> Iterator[Path]:
    logger.info("obsidian.scan root=%s", root)
    for path in root.rglob("*.md"):
        if path.is_file():
            logger.debug("obsidian.md=%s", path)
            yield path


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    header = text[4:end].splitlines()
    rest = text[end + 5 :]
    meta: Dict[str, str] = {}
    for ln in header:
        m = _FRONT_KEY_RE.match(ln.strip())
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
    logger.debug("obsidian.front keys=%s", list(meta.keys()))
    return meta, rest


def _first_h1(text: str) -> Optional[str]:
    m = _H1_RE.search(text)
    return m.group(1).strip() if m else None


def _group_blockquotes(lines: List[str]) -> List[Tuple[int, List[str]]]:
    groups: List[Tuple[int, List[str]]] = []
    buf: List[str] = []
    start = 0
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(">"):
            if not buf:
                start = i
            buf.append(ln)
        else:
            if buf:
                groups.append((start, buf))
                buf = []
    if buf:
        groups.append((start, buf))
    return groups


def _group_paragraphs(lines: List[str]) -> List[Tuple[int, List[str]]]:
    groups: List[Tuple[int, List[str]]] = []
    buf: List[str] = []
    start = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            if buf:
                groups.append((start, buf))
                buf = []
            continue
        # メタ行や見出しは除外
        if s.startswith("#") or re.match(r"^[A-Za-zぁ-んァ-ヶ一-龠0-9_\- ]+\s*:\s*", s):
            if buf:
                groups.append((start, buf))
                buf = []
            continue
        if not buf:
            start = i
        buf.append(ln)
    if buf:
        groups.append((start, buf))
    return groups


def _mk_id(path: Path, start_line: int, text: str) -> str:
    h = hashlib.sha1()
    h.update(str(path).encode("utf-8", errors="ignore"))
    h.update(str(start_line).encode("utf-8"))
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()


def parse_highlights_from_text(path: Path, text: str, root: Path) -> List[Highlight]:
    meta, body = _parse_frontmatter(text)
    title = meta.get("title") or _first_h1(body) or path.stem
    author = meta.get("author")
    asin = meta.get("asin")
    lines = body.splitlines()
    groups = _group_blockquotes(lines)
    if not groups:
        groups = _group_paragraphs(lines)
        logger.info(
            "obsidian.fallback paragraphs file=%s title=%s groups=%d",
            path,
            title,
            len(groups),
        )
    logger.info(
        "obsidian.parse file=%s title=%s author=%s groups=%d",
        path,
        title,
        author,
        len(groups),
    )
    result: List[Highlight] = []
    for start, g in groups:
        raw = "\n".join([re.sub(r"^\s*>\s?", "", ln) for ln in g]).strip()
        if not raw:
            continue
        # 短すぎる断片はノイズとして除外
        if len(raw) < 6:
            continue
        loc = None
        added = None
        tail = "\n".join(
            lines[min(len(lines) - 1, start + len(g)) : start + len(g) + 3]
        )
        m1 = _LOC_RE.search(raw) or _LOC_RE.search(tail)
        if m1:
            loc = m1.group(2)
        m2 = _ADDED_RE.search(raw) or _ADDED_RE.search(tail)
        if m2:
            added = m2.group(2).strip()
        hid = _mk_id(path, start, raw)
        rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        result.append(
            Highlight(
                id=hid,
                book=title,
                author=author,
                text=raw,
                location=loc,
                added_on=added,
                file=rel,
                asin=asin,
            )
        )
    logger.info("obsidian.parsed file=%s count=%d", path, len(result))
    return result


def parse_highlights_file(path: Path, root: Path) -> List[Highlight]:
    logger.debug("obsidian.read file=%s", path)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        logger.warning("obsidian.read_fail file=%s err=%r", path, exc)
        return []
    low = text.lower()
    if not ("kindle" in low or "readwise" in low or ">" in text):
        logger.debug("obsidian.skip file=%s", path)
        return []
    return parse_highlights_from_text(path, text, root)


def collect_highlights(root: Path) -> List[Highlight]:
    items: List[Highlight] = []
    count = 0
    for md in iter_md_files(root):
        count += 1
        items.extend(parse_highlights_file(md, root))
        if count % 200 == 0:
            logger.info("obsidian.progress scanned=%d highlights=%d", count, len(items))
    logger.info("obsidian.done scanned=%d highlights=%d", count, len(items))
    return items


def list_books_from_highlights(hl: Iterable[Highlight]) -> List[Dict[str, str]]:
    seen: Dict[Tuple[str, Optional[str]], int] = {}
    books: List[Dict[str, str]] = []
    for it in hl:
        key = (it.book, it.author)
        if key in seen:
            continue
        seen[key] = 1
        books.append({"title": it.book, "author": it.author or ""})
    books.sort(key=lambda x: (x["title"], x["author"]))
    logger.info("obsidian.books unique=%d", len(books))
    return books
