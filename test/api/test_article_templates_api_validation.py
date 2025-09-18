from ..helpers.common import create_test_client


def test_api_save_article_template_duplicate_key_returns_400():
    c = create_test_client()
    payload = {
        "name": "dup",
        "fields": [
            {"key": "url", "label": "URL", "input_type": "text"},
            {"key": "url", "label": "URL2", "input_type": "text"},
        ],
    }
    r = c.post("/api/article-templates/url", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "duplicate" in body.get("detail", "")


def test_api_save_article_template_too_many_fields_returns_400():
    c = create_test_client()
    fields = [
        {"key": f"k{i}", "label": f"L{i}", "input_type": "text"} for i in range(31)
    ]
    payload = {"name": "many", "fields": fields}
    r = c.post("/api/article-templates/note", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "too many" in body.get("detail", "")
