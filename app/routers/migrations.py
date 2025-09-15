from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.storage import get_article_template, get_prompt_template, save_article_template

router = APIRouter()


@router.post("/article-templates/{t}/migrate-from-prompt")
def migrate_article_template_from_prompt(t: str, payload: Dict[str, Any]) -> dict:
    name = str(payload.get("name", "")).strip()
    # delete_source: UI 側で旧テンプレ削除 API を個別に呼ぶ想定
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    base = get_article_template(t)
    if not base:
        raise HTTPException(status_code=404, detail="article template not found")
    src = get_prompt_template(name)
    if not src:
        raise HTTPException(status_code=404, detail="prompt template not found")
    merged = {
        "name": base.get("name", ""),
        "fields": base.get("fields", []),
        "prompt_template": src.get("content", ""),
    }
    row = save_article_template(t, merged)
    if not row:
        raise HTTPException(status_code=400, detail="invalid type")
    # delete_source は UI 側で /api/templates に対して個別に DELETE を呼ぶ想定
    return {"ok": True, "template": row}
