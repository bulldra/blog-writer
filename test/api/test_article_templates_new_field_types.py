from ..helpers.api import validate_template_response
from ..helpers.common import create_test_client


def test_save_article_template_with_date_and_select():
    c = create_test_client()
    payload = {
        "name": "with_date_select",
        "fields": [
            {"key": "publish_date", "label": "公開日", "input_type": "date"},
            {
                "key": "category",
                "label": "カテゴリ",
                "input_type": "select",
                "options": ["技術", "日記", "レビュー", "技術"],  # 重複含む→正規化
            },
            {"key": "body", "label": "本文", "input_type": "textarea"},
        ],
    }
    r = c.post("/api/article-templates/note", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    validate_template_response(data, "with_date_select")

    # select の options 正規化確認（重複除去）
    fields_by_key = {f["key"]: f for f in data["fields"]}
    assert fields_by_key["category"]["options"] == ["技術", "日記", "レビュー"]
    assert fields_by_key["publish_date"]["input_type"] == "date"


def test_save_article_template_select_without_options_fallbacks_to_text():
    c = create_test_client()
    payload = {
        "name": "invalid_select",
        "fields": [
            {
                "key": "empty_select",
                "label": "空セレクト",
                "input_type": "select",
                "options": [],
            },
        ],
    }
    r = c.post("/api/article-templates/note", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    fields_by_key = {f["key"]: f for f in data["fields"]}
    assert fields_by_key["empty_select"]["input_type"] == "text"
