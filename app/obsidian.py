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


@dataclass(frozen=True)
class ObsidianConfig:
    root_dir: Path
    articles_dir: str = "articles"
    highlights_dir: str = "kindle_highlights"
    
    @property
    def articles_path(self) -> Path:
        return self.root_dir / self.articles_dir
    
    @property
    def highlights_path(self) -> Path:
        return self.root_dir / self.highlights_dir


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


def get_configured_obsidian_config() -> Optional[ObsidianConfig]:
    """新しい設定構造でObsidian設定を取得"""
    cfg = _load_settings()
    
    # 新しい設定構造をチェック
    obsidian_cfg = cfg.get("obsidian")
    if isinstance(obsidian_cfg, dict):
        root_dir_val = obsidian_cfg.get("root_dir")
        if isinstance(root_dir_val, str) and root_dir_val.strip():
            root_path = Path(root_dir_val).expanduser().resolve()
            if root_path.exists() and root_path.is_dir():
                articles_dir = obsidian_cfg.get("articles_dir", "articles")
                highlights_dir = obsidian_cfg.get("highlights_dir", "kindle_highlights")
                if isinstance(articles_dir, str) and isinstance(highlights_dir, str):
                    return ObsidianConfig(
                        root_dir=root_path,
                        articles_dir=articles_dir,
                        highlights_dir=highlights_dir
                    )
            logger.warning("obsidian.config_invalid root_dir=%s", root_path)
    
    # 旧設定構造をチェック（下位互換性）
    old_dir = cfg.get("obsidian_dir")
    if isinstance(old_dir, str) and old_dir.strip():
        root_path = Path(old_dir).expanduser().resolve()
        if root_path.exists() and root_path.is_dir():
            return ObsidianConfig(root_dir=root_path)
        logger.warning("obsidian.config_invalid obsidian_dir=%s", root_path)
    
    return None


def set_configured_obsidian_config(
    root_dir: Optional[str],
    articles_dir: str = "articles", 
    highlights_dir: str = "kindle_highlights"
) -> Optional[ObsidianConfig]:
    """新しい設定構造でObsidian設定を保存"""
    cfg = _load_settings()
    if not isinstance(cfg, dict):
        cfg = {}
    
    if root_dir and root_dir.strip():
        root_path = Path(root_dir).expanduser().resolve()
        if not (root_path.exists() and root_path.is_dir()):
            raise OSError(f"Invalid directory: {root_path}")
        
        # 新しい設定構造で保存
        cfg["obsidian"] = {
            "root_dir": str(root_path),
            "articles_dir": articles_dir,
            "highlights_dir": highlights_dir
        }
        
        # 旧設定を削除（クリーンアップ）
        cfg.pop("obsidian_dir", None)
        
        _save_settings(cfg)
        return ObsidianConfig(
            root_dir=root_path,
            articles_dir=articles_dir,
            highlights_dir=highlights_dir
        )
    
    # クリア
    cfg.pop("obsidian", None)
    cfg.pop("obsidian_dir", None)  # 旧設定もクリア
    _save_settings(cfg)
    return None


def get_configured_obsidian_dir() -> Optional[Path]:
    """下位互換性のための関数"""
    config = get_configured_obsidian_config()
    return config.root_dir if config else None


def set_configured_obsidian_dir(path: Optional[str]) -> Optional[Path]:
    """下位互換性のための関数"""
    config = set_configured_obsidian_config(path)
    return config.root_dir if config else None


def find_obsidian_highlights_dir() -> Optional[Path]:
    """Kindleハイライト用ディレクトリを取得"""
    config = get_configured_obsidian_config()
    if config:
        highlights_path = config.highlights_path
        if highlights_path.exists() and highlights_path.is_dir():
            return highlights_path
        logger.warning("obsidian.highlights_dir_not_found path=%s", highlights_path)
    
    # フォールバック: 旧形式での探索
    root = find_obsidian_dir()
    if root:
        for candidate in [root / "kindle_highlights", root / "kindle_highlight"]:
            if candidate.exists() and candidate.is_dir():
                return candidate
    
    return None


def find_obsidian_articles_dir() -> Optional[Path]:
    """過去記事用ディレクトリを取得"""
    config = get_configured_obsidian_config()
    if config:
        articles_path = config.articles_path
        if articles_path.exists() and articles_path.is_dir():
            return articles_path
        logger.warning("obsidian.articles_dir_not_found path=%s", articles_path)
    
    # フォールバック: ルートディレクトリを返す
    return find_obsidian_dir()


def find_obsidian_dir(data_dir: Path | None = None) -> Optional[Path]:
    # 設定があれば最優先
    config = get_configured_obsidian_config()
    if config:
        logger.info("obsidian.use_config dir=%s", config.root_dir)
        return config.root_dir
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


def collect_highlights(root: Optional[Path] = None) -> List[Highlight]:
    """ハイライトを収集（新しいディレクトリ構造対応）"""
    if root is None:
        root = find_obsidian_highlights_dir()
        if not root:
            logger.warning("obsidian.no_highlights_dir")
            return []
    
    items: List[Highlight] = []
    count = 0
    for md in iter_md_files(root):
        count += 1
        items.extend(parse_highlights_file(md, root))
        if count % 200 == 0:
            logger.info("obsidian.progress scanned=%d highlights=%d", count, len(items))
    logger.info("obsidian.done scanned=%d highlights=%d", count, len(items))
    return items


def collect_articles(root: Optional[Path] = None) -> List[Path]:
    """過去記事ファイルを収集"""
    if root is None:
        root = find_obsidian_articles_dir()
        if not root:
            logger.warning("obsidian.no_articles_dir")
            return []
    
    articles: List[Path] = []
    for md in iter_md_files(root):
        # ハイライトファイルでないものを記事として扱う
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
            low = text.lower()
            # Kindleハイライト系のキーワードがなければ記事とみなす
            if not ("kindle" in low or "readwise" in low or 
                   (text.count(">") > len(text.splitlines()) * 0.3)):
                articles.append(md)
        except OSError as exc:
            logger.debug("obsidian.article_check_error file=%s err=%r", md, exc)
    
    logger.info("obsidian.articles_found count=%d", len(articles))
    return articles


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
