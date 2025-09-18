"""AI Router機能の追加テスト"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..helpers.common import create_test_client


def test_ai_generate_basic():
    """AI生成APIの基本テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "生成されたテキスト"

        response = client.post("/api/ai/generate", json={"prompt": "テストプロンプト"})

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["text"] == "生成されたテキスト"


def test_ai_generate_with_url_context():
    """URL コンテキスト付きAI生成テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        with patch("app.routers.ai.fetch_url_context") as mock_fetch:
            mock_fetch.return_value = "URLの内容"
            mock_ai.return_value = "生成されたテキスト"

            response = client.post(
                "/api/ai/generate",
                json={
                    "prompt": "テストプロンプト",
                    "url_context": "https://example.com",
                },
            )

            assert response.status_code == 200
            mock_fetch.assert_called_once_with("https://example.com")


def test_ai_generate_with_highlights():
    """ハイライト付きAI生成テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "生成されたテキスト"

        response = client.post(
            "/api/ai/generate",
            json={
                "prompt": "テストプロンプト",
                "highlights": ["ハイライト1", "ハイライト2"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data


def test_ai_generate_with_rag():
    """RAG検索付きAI生成テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        with patch("app.routers.ai.get_rag_manager") as mock_get_rag:
            mock_rag = Mock()
            mock_rag.search_all_books.return_value = {
                "test_book": [("テスト内容", {"book": "test"}, 0.8)]
            }
            mock_rag.format_search_results.return_value = "検索結果"
            mock_get_rag.return_value = mock_rag
            mock_ai.return_value = "生成されたテキスト"

            response = client.post(
                "/api/ai/generate",
                json={"prompt": "テストプロンプト", "enable_rag": True},
            )

            assert response.status_code == 200


def test_ai_generate_error_handling():
    """AI生成エラーハンドリングテスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.side_effect = Exception("AI service error")

        response = client.post("/api/ai/generate", json={"prompt": "テストプロンプト"})

        assert response.status_code == 500


def test_ai_generate_missing_prompt():
    """プロンプト未指定のテスト"""
    client = create_test_client()

    response = client.post("/api/ai/generate", json={})

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_ai_edit_stream():
    """AI編集ストリーミングテスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai_stream") as mock_stream:

        async def mock_generator():
            yield "編集された"
            yield "テキスト"

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/api/ai/edit/stream",
            json={"content": "元のテキスト", "instruction": "編集指示"},
        )

        assert response.status_code == 200
        # ストリーミングレスポンスの詳細チェックは実装依存


def test_ai_widget_suggestions():
    """AIウィジェット提案テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "提案されたコンテンツ"

        response = client.post(
            "/api/ai/widget-suggestions",
            json={
                "widgets": ["kindle", "url_context"],
                "context": {"title": "テストタイトル"},
            },
        )

        assert response.status_code == 200


def test_ai_from_bullets_prompt():
    """箇条書きからプロンプト生成テスト"""
    client = create_test_client()

    response = client.post(
        "/api/ai/from-bullets/prompt",
        json={"bullets": ["項目1", "項目2", "項目3"], "title": "テストタイトル"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "prompt" in data


def test_ai_from_bullets_stream():
    """箇条書きからストリーミング生成テスト"""
    client = create_test_client()

    with patch("app.routers.ai.call_ai_stream") as mock_stream:

        async def mock_generator():
            yield "[Reasoning]\n推論内容\n[生成結果]\n"
            yield "生成されたコンテンツ"

        mock_stream.return_value = mock_generator()

        response = client.post(
            "/api/ai/from-bullets/stream",
            json={"bullets": ["項目1", "項目2"], "title": "テストタイトル"},
        )

        assert response.status_code == 200
