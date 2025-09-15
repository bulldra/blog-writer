from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage import (
    cleanup_prompt_templates,
    delete_prompt_template,
    list_prompt_templates,
    save_prompt_template,
)

router = APIRouter()


class TemplatePayload(BaseModel):
    name: str
    content: str


@router.get("")
def list_all() -> List[dict]:
    return list_prompt_templates()


@router.post("")
def upsert(payload: TemplatePayload) -> dict:
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    row = save_prompt_template(name, payload.content or "")
    return row


@router.delete("")
def remove(name: str) -> dict:
    ok = delete_prompt_template(name)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


@router.post("/cleanup")
def cleanup() -> dict:
    removed = cleanup_prompt_templates()
    return {"removed": removed}
