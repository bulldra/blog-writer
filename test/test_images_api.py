from app.routers.images import EyecatchRequest, generate_eyecatch


def test_generate_eyecatch_basic():
    req = EyecatchRequest(title="テスト", width=800, height=418, theme="dark")
    res = generate_eyecatch(req)
    assert isinstance(res, dict)
    assert res.get("content_type") == "image/svg+xml"
    data_url = res.get("data_url") or ""
    assert data_url.startswith("data:image/svg+xml;base64,")
    # base64の中身がそれっぽい長さ
    assert len(data_url) > 200
