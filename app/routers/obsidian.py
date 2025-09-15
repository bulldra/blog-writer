from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.obsidian import (
    collect_articles,
    collect_highlights,
    find_obsidian_articles_dir,
    find_obsidian_dir,
    find_obsidian_highlights_dir,
    get_configured_obsidian_config,
    list_books_from_highlights,
    set_configured_obsidian_config,
)

router = APIRouter()


class ObsidianConfigRequest(BaseModel):
    root_dir: Optional[str] = None
    articles_dir: str = "articles"
    highlights_dir: str = "kindle_highlights"


@router.get("/health")
def health():
    root = find_obsidian_dir()
    highlights_dir = find_obsidian_highlights_dir()
    articles_dir = find_obsidian_articles_dir()
    return {
        "obsidianDir": str(root) if root else None,
        "highlightsDir": str(highlights_dir) if highlights_dir else None,
        "articlesDir": str(articles_dir) if articles_dir else None,
    }


@router.get("/config")
def get_config():
    config = get_configured_obsidian_config()
    if config:
        return {
            "rootDir": str(config.root_dir),
            "articlesDir": config.articles_dir,
            "highlightsDir": config.highlights_dir,
        }

    return {"rootDir": None, "articlesDir": None, "highlightsDir": None}


@router.post("/config")
def set_config(config_req: ObsidianConfigRequest):
    try:
        config = set_configured_obsidian_config(
            config_req.root_dir, config_req.articles_dir, config_req.highlights_dir
        )
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 現在の有効な設定を返す
    effective_config = get_configured_obsidian_config()
    highlights_dir = find_obsidian_highlights_dir()
    articles_dir = find_obsidian_articles_dir()

    return {
        "configured": (
            {
                "rootDir": str(config.root_dir) if config else None,
                "articlesDir": config.articles_dir if config else None,
                "highlightsDir": config.highlights_dir if config else None,
            }
            if config
            else None
        ),
        "effective": {
            "rootDir": str(effective_config.root_dir) if effective_config else None,
            "highlightsDir": str(highlights_dir) if highlights_dir else None,
            "articlesDir": str(articles_dir) if articles_dir else None,
        },
    }


@router.get("/books")
def list_books():
    highlights_dir = find_obsidian_highlights_dir()
    if not highlights_dir:
        root = find_obsidian_dir()
        if not root:
            raise HTTPException(
                status_code=404,
                detail="obsidian dir not found; highlights dir not found",
            )
        items = collect_highlights()
    else:
        items = collect_highlights(highlights_dir)
    return list_books_from_highlights(items)


@router.get("/highlights")
def list_highlights(book: Optional[str] = Query(None)) -> List[dict]:
    highlights_dir = find_obsidian_highlights_dir()
    if not highlights_dir:
        root = find_obsidian_dir()
        if not root:
            raise HTTPException(
                status_code=404,
                detail="obsidian dir not found; highlights dir not found",
            )
        items = collect_highlights()
    else:
        items = collect_highlights(highlights_dir)
    rows = [
        {
            "id": it.id,
            "book": it.book,
            "author": it.author,
            "text": it.text,
            "location": it.location,
            "added_on": it.added_on,
            "file": it.file,
            "asin": it.asin,
        }
        for it in items
        if (not book or it.book == book)
    ]
    return rows


@router.get("/articles")
def list_articles() -> List[dict]:
    """過去記事一覧を取得"""
    articles_dir = find_obsidian_articles_dir()
    if not articles_dir:
        raise HTTPException(status_code=404, detail="obsidian articles dir not found")

    articles = collect_articles(articles_dir)
    return [
        {
            "path": str(article),
            "name": article.stem,
            "relative_path": (
                str(article.relative_to(articles_dir))
                if article.is_relative_to(articles_dir)
                else str(article)
            ),
        }
        for article in articles
    ]
