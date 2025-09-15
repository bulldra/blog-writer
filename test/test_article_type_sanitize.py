from app.routers.ai import BulletsRequest, _sanitize_bullets_request


def test_article_type_note_disables_all_external():
    req = BulletsRequest(
        bullets=["a"],
        url_context="https://example.com",
        highlights=["h"],
        article_type="note",
    )
    out = _sanitize_bullets_request(req)
    assert out.url_context is None
    assert out.highlights is None
    assert out.highlights_asin is None


def test_article_type_url_disables_highlights():
    req = BulletsRequest(
        bullets=["a"],
        url_context="https://example.com",
        highlights=["h"],
        article_type="url",
    )
    out = _sanitize_bullets_request(req)
    assert out.url_context == "https://example.com"
    assert out.highlights is None
    assert out.highlights_asin is None


def test_article_type_review_disables_url():
    req = BulletsRequest(
        bullets=["a"],
        url_context="https://example.com",
        highlights=["h"],
        article_type="review",
    )
    out = _sanitize_bullets_request(req)
    assert out.url_context is None
    assert out.highlights == ["h"]
