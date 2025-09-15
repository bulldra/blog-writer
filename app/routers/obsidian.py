from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.obsidian import (
    collect_highlights,
    find_obsidian_dir,
    get_configured_obsidian_dir,
    list_books_from_highlights,
    set_configured_obsidian_dir,
)

router = APIRouter()


@router.get("/health")
def health():
    root = find_obsidian_dir()
    return {"obsidianDir": str(root) if root else None}


@router.get("/config")
def get_config():
    p = get_configured_obsidian_dir()
    return {"obsidianDir": str(p) if p else None}


@router.post("/config")
def set_config(
    path: Optional[str] = Query(
        None, description="Obsidian ディレクトリの絶対パス。空でクリア"
    )
):
    try:
        p = set_configured_obsidian_dir(path)
    except OSError as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    root = find_obsidian_dir()
    return {
        "configured": str(p) if p else None,
        "effective": str(root) if root else None,
    }


@router.get("/books")
def list_books():
    root = find_obsidian_dir()
    if not root:
        raise HTTPException(status_code=404, detail="obsidian dir not found")
    items = collect_highlights(root)
    return list_books_from_highlights(items)


@router.get("/highlights")
def list_highlights(book: Optional[str] = Query(None)) -> List[dict]:
    root = find_obsidian_dir()
    if not root:
        raise HTTPException(status_code=404, detail="obsidian dir not found")
    items = collect_highlights(root)
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
