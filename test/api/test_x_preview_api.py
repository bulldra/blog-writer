from fastapi.testclient import TestClient

from app.main import create_app


def test_x_preview_api_with_raw_posts():
    app = create_app()
    client = TestClient(app)

    payload = {
        "mode": "thread",
        "max_posts": 3,
        "raw_posts": [
            {"id": "1", "text": "Hello", "author": "alice", "created_at": "2024-01-01"},
            {"id": "2", "text": "World"},
        ],
    }

    resp = client.post("/api/widgets/x/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    text = data.get("text", "")
    assert "@alice" in text
    assert "> Hello" in text
    assert "> World" in text
