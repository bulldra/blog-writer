from fastapi.testclient import TestClient

from app.main import create_app


def test_save_generation_history_api():
    """生成履歴保存APIのテスト"""
    app = create_app()
    client = TestClient(app)

    payload = {
        "title": "APIテスト記事",
        "template_type": "api_test",
        "widgets_used": ["properties", "url_context"],
        "properties": {"theme": "APIテスト", "goal": "テスト成功"},
        "generated_content": "APIで保存されたテストコンテンツです。",
        "reasoning": "APIテスト用の思考過程",
    }

    response = client.post("/api/generation-history", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "APIテスト記事"
    assert data["template_type"] == "api_test"
    assert data["widgets_used"] == ["properties", "url_context"]
    assert data["properties"] == {"theme": "APIテスト", "goal": "テスト成功"}
    assert data["generated_content"] == "APIで保存されたテストコンテンツです。"
    assert data["reasoning"] == "APIテスト用の思考過程"
    assert "id" in data
    assert "created_at" in data


def test_list_generation_history_api():
    """生成履歴一覧取得APIのテスト"""
    app = create_app()
    client = TestClient(app)

    # 先にいくつか履歴を保存
    for i in range(3):
        payload = {
            "title": f"リスト用記事{i}",
            "template_type": "list_test",
            "widgets_used": ["properties"],
            "properties": {"index": str(i)},
            "generated_content": f"リスト用コンテンツ{i}",
        }
        client.post("/api/generation-history", json=payload)

    # 履歴一覧を取得
    response = client.get("/api/generation-history")
    assert response.status_code == 200

    data = response.json()
    assert "history" in data
    histories = data["history"]
    assert isinstance(histories, list)
    assert len(histories) >= 3

    # 各履歴アイテムの構造確認
    for history in histories:
        assert "id" in history
        assert "title" in history
        assert "template_type" in history
        assert "widgets_used" in history
        assert "properties" in history
        assert "created_at" in history
        assert "content_length" in history


def test_get_generation_history_detail_api():
    """特定の生成履歴詳細取得APIのテスト"""
    app = create_app()
    client = TestClient(app)

    # 履歴を保存
    payload = {
        "title": "詳細取得テスト",
        "template_type": "detail_test",
        "widgets_used": ["kindle"],
        "properties": {"book": "テスト本"},
        "generated_content": "詳細取得用のコンテンツです。",
        "reasoning": "詳細取得テスト用思考",
    }

    save_response = client.post("/api/generation-history", json=payload)
    assert save_response.status_code == 200
    saved_data = save_response.json()
    history_id = saved_data["id"]

    # 詳細を取得
    detail_response = client.get(f"/api/generation-history/{history_id}")
    assert detail_response.status_code == 200

    detail_data = detail_response.json()
    assert detail_data["id"] == history_id
    assert detail_data["title"] == "詳細取得テスト"
    assert detail_data["template_type"] == "detail_test"
    assert detail_data["widgets_used"] == ["kindle"]
    assert detail_data["properties"] == {"book": "テスト本"}
    assert detail_data["generated_content"] == "詳細取得用のコンテンツです。"
    assert detail_data["reasoning"] == "詳細取得テスト用思考"


def test_delete_generation_history_api():
    """生成履歴削除APIのテスト"""
    app = create_app()
    client = TestClient(app)

    # 履歴を保存
    payload = {
        "title": "削除テスト",
        "template_type": "delete_test",
        "widgets_used": [],
        "properties": {},
        "generated_content": "削除される予定のコンテンツ",
    }

    save_response = client.post("/api/generation-history", json=payload)
    assert save_response.status_code == 200
    saved_data = save_response.json()
    history_id = saved_data["id"]

    # 削除前に存在することを確認
    get_response = client.get(f"/api/generation-history/{history_id}")
    assert get_response.status_code == 200

    # 削除
    delete_response = client.delete(f"/api/generation-history/{history_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True

    # 削除後は404になる
    get_after_delete = client.get(f"/api/generation-history/{history_id}")
    assert get_after_delete.status_code == 404


def test_get_nonexistent_history_api():
    """存在しない履歴の取得APIテスト"""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/generation-history/999999")
    assert response.status_code == 404


def test_delete_nonexistent_history_api():
    """存在しない履歴の削除APIテスト"""
    app = create_app()
    client = TestClient(app)

    response = client.delete("/api/generation-history/999999")
    assert response.status_code == 404


def test_generation_history_with_limit_param():
    """履歴一覧取得でlimitパラメータのテスト"""
    app = create_app()
    client = TestClient(app)

    # 複数履歴を保存
    for i in range(5):
        payload = {
            "title": f"制限テスト{i}",
            "template_type": "limit_test",
            "widgets_used": [],
            "properties": {},
            "generated_content": f"制限テストコンテンツ{i}",
        }
        client.post("/api/generation-history", json=payload)

    # limit=2で取得
    response = client.get("/api/generation-history?limit=2")
    assert response.status_code == 200

    data = response.json()
    histories = data["history"]
    assert len(histories) == 2
