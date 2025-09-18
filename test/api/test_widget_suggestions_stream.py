from unittest.mock import AsyncMock, patch

from ..helpers.common import create_test_client


def test_widget_suggestions_stream_basic():
    client = create_test_client()

    async def fake_stream(_prompt: str):  # noqa: ANN001
        yield "提案1"
        yield "提案2"

    with patch("app.routers.ai.call_ai_stream", new_callable=AsyncMock) as mock_stream:
        mock_stream.return_value = fake_stream("p")
        resp = client.post(
            "/api/ai/widget-suggestions/stream",
            json={"widgets": ["url_context"], "context": {"title": "T"}},
        )
        assert resp.status_code == 200
        text = resp.text.strip().splitlines()
        assert "提案1" in text[0]
        assert "提案2" in text[1]


def test_widget_suggestions_stream_stub():
    client = create_test_client()
    # パッチしない=スタブ
    resp = client.post(
        "/api/ai/widget-suggestions/stream",
        json={"widgets": ["kindle"], "context": {"title": "X"}},
    )
    assert resp.status_code == 200
    assert "stub" in resp.text
