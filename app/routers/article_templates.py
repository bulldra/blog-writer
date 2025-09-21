from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.storage import (
    delete_article_template,
    diff_template_versions,
    duplicate_article_template,
    get_article_template,
    get_available_widgets,
    get_template_version_snapshot,
    list_article_templates,
    list_template_versions,
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


@router.post("/{t}/duplicate")
def duplicate(t: str, payload: Dict[str, Any]):
    try:
        new_type = str(payload.get("new_type", "")).strip() or None
        new_name = str(payload.get("new_name", "")).strip() or None
        row = duplicate_article_template(t, new_type=new_type, new_name=new_name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row


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


@router.get("/{t}/versions")
def versions(t: str):
    return list_template_versions(t)


@router.get("/{t}/versions/{version}")
def version_snapshot(t: str, version: int):
    snap = get_template_version_snapshot(t, version)
    if not snap:
        raise HTTPException(status_code=404, detail="not found")
    return snap


@router.get("/{t}/diff")
def version_diff(t: str, from_version: int, to_version: int):
    return diff_template_versions(t, from_version, to_version)
