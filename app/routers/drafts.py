from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage import create_draft as store_create
from app.storage import delete_draft as store_delete
from app.storage import (
    delete_markdown_post,
    list_markdown_posts,
    read_markdown_post,
    save_markdown_post,
)
from app.storage import get_draft as store_get
from app.storage import list_drafts as store_list
from app.storage import update_draft as store_update

router = APIRouter()


class DraftCreate(BaseModel):
    title: str
    content: str


class DraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class MarkdownSave(BaseModel):
    content: str
    git_commit: Optional[bool] = False


@router.post("/save-markdown")
def save_markdown(payload: MarkdownSave) -> dict:
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="content is required")
    info = save_markdown_post(payload.content, bool(payload.git_commit))
    return {"ok": True, **info}


@router.get("/posts")
def list_posts() -> List[dict]:
    return list_markdown_posts()


@router.get("/posts/{filename}")
def get_post(filename: str) -> dict:
    content = read_markdown_post(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="post not found")
    return {"filename": filename, "content": content}


@router.delete("/posts/{filename}")
def delete_post(filename: str) -> dict:
    ok = delete_markdown_post(filename)
    if not ok:
        raise HTTPException(status_code=404, detail="post not found")
    return {"ok": True}


@router.get("")
def list_drafts() -> List[dict]:
    return store_list()


@router.post("")
def create_draft(payload: DraftCreate) -> dict:
    return store_create(payload.title.strip() or "無題", payload.content)


@router.get("/{draft_id}")
def get_draft(draft_id: int) -> dict:
    row = store_get(draft_id)
    if not row:
        raise HTTPException(status_code=404, detail="draft not found")
    return row


@router.put("/{draft_id}")
def update_draft(draft_id: int, payload: DraftUpdate) -> dict:
    row = store_update(draft_id, payload.title, payload.content)
    if not row:
        raise HTTPException(status_code=404, detail="draft not found")
    return row


@router.delete("/{draft_id}")
def delete_draft(draft_id: int):
    ok = store_delete(draft_id)
    if not ok:
        raise HTTPException(status_code=404, detail="draft not found")
    return {"ok": True}
