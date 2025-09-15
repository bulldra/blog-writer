from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage import create_phrase as store_create
from app.storage import delete_phrase as store_delete
from app.storage import list_phrases as store_list

router = APIRouter()


class Phrase(BaseModel):
    id: int
    text: str
    note: Optional[str] = None


class PhraseCreate(BaseModel):
    text: str
    note: Optional[str] = None


@router.get("")
async def list_phrases() -> List[Phrase]:
    return [Phrase(**row) for row in store_list()]


@router.post("")
async def create_phrase(payload: PhraseCreate) -> Phrase:
    row = store_create(payload.text, payload.note)
    return Phrase(**row)


@router.delete("/{phrase_id}")
async def delete_phrase(phrase_id: int) -> dict:
    ok = store_delete(phrase_id)
    if not ok:
        raise HTTPException(status_code=404, detail="phrase not found")
    return {"ok": True}
