"""文体テンプレート管理のAPIエンドポイント"""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai_utils import analyze_writing_style
from app.storage import (
    delete_writing_style,
    get_writing_style,
    list_writing_styles,
    save_writing_style,
)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str


@router.get("")
def list_all():
    """文体テンプレート一覧を取得"""
    return list_writing_styles()


@router.get("/{style_id}")
def get_one(style_id: str):
    """指定された文体テンプレートを取得"""
    style = get_writing_style(style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Writing style not found")
    return style


@router.post("/{style_id}")
def save_one(style_id: str, payload: Dict[str, Any]):
    """文体テンプレートを保存"""
    try:
        style = save_writing_style(style_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not style:
        raise HTTPException(status_code=400, detail="Invalid writing style data")
    return style


@router.delete("/{style_id}")
def delete_one(style_id: str):
    """文体テンプレートを削除"""
    ok = delete_writing_style(style_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Writing style not found")
    return {"ok": True}


@router.post("/analyze")
async def analyze_text(req: AnalyzeRequest):
    """文章を分析して文体の特徴を抽出"""
    if not req.text or len(req.text.strip()) < 50:
        raise HTTPException(
            status_code=400, 
            detail="Text must be at least 50 characters long"
        )
    
    result = await analyze_writing_style(req.text)
    if result is None:
        raise HTTPException(
            status_code=500, 
            detail="Failed to analyze writing style"
        )
    
    return {"analysis": result}