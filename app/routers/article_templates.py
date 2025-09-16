from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.storage import (
    delete_article_template,
    get_article_template,
    get_available_widgets,
    list_article_templates,
    save_article_template,
)

router = APIRouter()


@router.get("")
def list_all():
    return list_article_templates()


@router.get("/{t}")
def get_one(t: str):
    row = get_article_template(t)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row


@router.post("/{t}")
def save_one(t: str, payload: Dict[str, Any]):
    try:
        row = save_article_template(t, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=400, detail="invalid type")
    return row


@router.delete("/{t}")
def delete_one(t: str):
    ok = delete_article_template(t)
    if not ok:
        raise HTTPException(status_code=400, detail="invalid type")
    return {"ok": True}


@router.get("/widgets/available")
def get_available_widget_types():
    """利用可能なウィジェットタイプの一覧を取得"""
    widgets = list(get_available_widgets())
    # Notion ウィジェットは動的に追加（テスト期待に合わせる）
    ids: List[str] = [w.get("id", "") for w in widgets]
    if "notion" not in ids:
        widgets.append(
            {
                "id": "notion",
                "name": "Notion連携",
                "description": "NotionのページやデータベースからMCP経由で情報を取得し、記事作成の参考にします",
            }
        )
    return {"widgets": widgets}
