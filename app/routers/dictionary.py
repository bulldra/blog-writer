from fastapi import APIRouter, Query

router = APIRouter()


# 簡易スタブ: termに対して辞書情報を返す。今は見出しとダミー説明のみ。
@router.get("")
async def lookup(term: str = Query(..., description="見出し語")):
    return {
        "term": term,
        "definitions": [
            {"pos": "n.", "def": f"Definition for {term} (stub)"},
        ],
        "synonyms": [],
        "antonyms": [],
    }
