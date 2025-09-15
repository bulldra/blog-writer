from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage import (
    delete_generation_history,
    get_generation_history,
    list_generation_history,
    save_generation_history,
)

router = APIRouter()


class GenerationHistoryRequest(BaseModel):
    title: str
    template_type: str
    widgets_used: List[str]
    properties: Dict[str, str]
    generated_content: str
    reasoning: str = ""


@router.get("")
def list_history(limit: int = 20):
    """生成履歴一覧の取得"""
    return {"history": list_generation_history(limit)}


@router.post("")
def save_history(request: GenerationHistoryRequest):
    """生成履歴の保存"""
    result = save_generation_history(
        title=request.title,
        template_type=request.template_type,
        widgets_used=request.widgets_used,
        properties=request.properties,
        generated_content=request.generated_content,
        reasoning=request.reasoning,
    )
    return result


@router.get("/{history_id}")
def get_history_detail(history_id: int):
    """特定の生成履歴の詳細取得"""
    result = get_generation_history(history_id)
    if not result:
        raise HTTPException(status_code=404, detail="History not found")
    return result


@router.delete("/{history_id}")
def delete_history(history_id: int):
    """生成履歴の削除"""
    success = delete_generation_history(history_id)
    if not success:
        raise HTTPException(status_code=404, detail="History not found")
    return {"ok": True}
