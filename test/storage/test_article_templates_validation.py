import pytest

from app.storage import save_article_template


def test_article_templates_duplicate_key_raises():
    with pytest.raises(ValueError):
        save_article_template(
            "url",
            {
                "name": "dup",
                "fields": [
                    {"key": "url", "label": "URL", "input_type": "text"},
                    {"key": "url", "label": "URL2", "input_type": "text"},
                ],
            },
        )


def test_article_templates_too_many_fields_raise():
    fields = [
        {"key": f"k{i}", "label": f"L{i}", "input_type": "text"} for i in range(31)
    ]
    with pytest.raises(ValueError):
        save_article_template("note", {"name": "many", "fields": fields})
