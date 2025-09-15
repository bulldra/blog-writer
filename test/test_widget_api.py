from fastapi.testclient import TestClient

from app.main import create_app


def test_get_available_widgets_api():
    """利用可能なウィジェット一覧取得APIのテスト"""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/api/article-templates/widgets/available")
    assert response.status_code == 200
    
    data = response.json()
    assert "widgets" in data
    widgets = data["widgets"]
    
    assert isinstance(widgets, list)
    assert len(widgets) == 4
    
    widget_ids = [w["id"] for w in widgets]
    assert set(widget_ids) == {"properties", "url_context", "kindle", "past_posts"}
    
    for widget in widgets:
        assert "id" in widget
        assert "name" in widget
        assert "description" in widget
        assert isinstance(widget["id"], str)
        assert isinstance(widget["name"], str)
        assert isinstance(widget["description"], str)


def test_save_template_with_widgets_api():
    """ウィジェット付きテンプレート保存APIのテスト"""
    app = create_app()
    client = TestClient(app)
    
    payload = {
        "name": "API ウィジェットテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["url_context", "kindle"],
    }
    
    response = client.post("/api/article-templates/api_test", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["widgets"] == ["url_context", "kindle"]
    
    # 保存されたテンプレートを取得して確認
    get_response = client.get("/api/article-templates/api_test")
    assert get_response.status_code == 200
    
    saved_data = get_response.json()
    assert saved_data["widgets"] == ["url_context", "kindle"]


def test_save_template_widget_order_via_api():
    """API経由でのウィジェット順序保持テスト"""
    app = create_app()
    client = TestClient(app)
    
    payload = {
        "name": "API 順序テスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["past_posts", "url_context", "kindle"],
    }
    
    response = client.post("/api/article-templates/api_order_test", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["widgets"] == ["past_posts", "url_context", "kindle"]
    
    # 順序が保持されているか確認
    get_response = client.get("/api/article-templates/api_order_test")
    assert get_response.status_code == 200
    
    saved_data = get_response.json()
    assert saved_data["widgets"] == ["past_posts", "url_context", "kindle"]