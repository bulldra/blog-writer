from app.main import create_app
from app.storage import get_article_template, save_prompt_template


def _client():
    from fastapi.testclient import TestClient

    app = create_app()
    return TestClient(app)


def test_migrate_article_template_from_prompt_success(tmp_path, monkeypatch):
    c = _client()
    # まず旧テンプレを保存
    save_prompt_template("legacy", "LEGACY_PROMPT")
    # マイグレーション呼び出し
    r = c.post(
        "/api/migrate/article-templates/review/migrate-from-prompt",
        json={"name": "legacy"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    # 記事テンプレ側へ内容が反映
    at = get_article_template("review")
    assert at and at.get("prompt_template") == "LEGACY_PROMPT"


def test_migrate_article_template_from_prompt_not_found():
    c = _client()
    r = c.post(
        "/api/migrate/article-templates/url/migrate-from-prompt",
        json={"name": "does-not-exist"},
    )
    assert r.status_code == 404
    assert "prompt template not found" in r.text
