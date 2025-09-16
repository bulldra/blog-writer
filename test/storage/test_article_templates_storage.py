from typing import Any, Dict

from app.storage import (
    delete_article_template,
    get_article_template,
    list_article_templates,
    save_article_template,
)


def test_article_templates_defaults_present():
    rows = list_article_templates()
    types = [r.get("type") for r in rows]
    assert set(types) >= {"url", "note", "review"}
    # 各テンプレの必須キーが存在
    for t in ("url", "note", "review"):
        row = get_article_template(t)
        assert row is not None
        assert row.get("name")
        assert isinstance(row.get("fields"), list)


def test_article_templates_save_and_override_and_delete():
    # save: url を上書き
    payload: Dict[str, Any] = {
        "name": "URL 改",
        "fields": [
            {"key": "goal", "label": "目的", "input_type": "text"},
            {"key": "url", "label": "URL", "input_type": "text"},
        ],
        "prompt_template": "{{base}}\n---\nURL={{url_context}}",
    }
    row = save_article_template("url", payload)
    assert row is not None
    assert row.get("name") == "URL 改"
    assert isinstance(row.get("fields"), list)
    assert row.get("prompt_template", "").endswith("{{url_context}}")

    # 上書き確認
    again = get_article_template("url")
    assert again is not None
    assert again.get("name") == "URL 改"

    # delete: 初期状態へ戻る（exists=True扱い）
    ok = delete_article_template("url")
    assert ok is True
    after = get_article_template("url")
    assert after is not None
    assert after.get("name") != "URL 改"  # 初期化されている
