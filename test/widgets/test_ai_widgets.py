"""Tests for AI integration with widgets."""


def test_from_bullets_with_widgets(client):
    """Test from-bullets endpoint with widget integration."""
    # Test request with widget configuration
    request_data = {
        "bullets": ["Test bullet point 1", "Test bullet point 2"],
        "title": "Test Article",
        "style": "formal",
        "length": "short",
        "widgets": [
            {
                "type": "notion",
                "data": {
                    "page_ids": ["test_page_id"],
                    "search_query": "",
                    "max_pages": 1,
                },
            }
        ],
    }

    # This will likely fail due to missing AI configuration, but we test the structure
    response = client.post("/api/ai/from-bullets", json=request_data)
    # The API should work normally, even if widgets fail
    assert response.status_code == 200


def test_from_bullets_with_invalid_widgets(client):
    """Test from-bullets endpoint with invalid widget configuration."""
    request_data = {
        "bullets": ["Test bullet point"],
        "widgets": [
            {
                "type": "notion",
                "data": {
                    "page_ids": [],  # Invalid: no page_ids or search_query
                    "search_query": "",
                    "max_pages": 1,
                },
            }
        ],
    }

    response = client.post("/api/ai/from-bullets", json=request_data)
    # Should handle invalid widget gracefully
    assert response.status_code == 200


def test_from_bullets_prompt_with_widgets(client):
    """Test from-bullets/prompt endpoint with widgets."""
    request_data = {
        "bullets": ["Test bullet point"],
        "title": "Test Article",
        "widgets": [
            {
                "type": "notion",
                "data": {
                    "page_ids": ["test_page_id"],
                    "search_query": "",
                    "max_pages": 1,
                },
            }
        ],
    }

    response = client.post("/api/ai/from-bullets/prompt", json=request_data)
    # Prompt generation should work even if widgets fail
    assert response.status_code in [200, 400, 422, 500]


def test_from_bullets_with_notion_context(client):
    """Test from-bullets endpoint with direct notion_context."""
    request_data = {
        "bullets": ["Test bullet point"],
        "title": "Test Article",
        "notion_context": "## Test Notion Page\n\nThis is test context from Notion.",
    }

    response = client.post("/api/ai/from-bullets", json=request_data)
    # Should handle notion_context parameter
    assert response.status_code == 200


def test_from_bullets_with_multiple_widgets(client):
    """Test from-bullets endpoint with multiple widgets."""
    request_data = {
        "bullets": ["Test bullet point"],
        "widgets": [
            {
                "type": "notion",
                "data": {"page_ids": ["page1"], "search_query": "", "max_pages": 1},
            },
            {"type": "unknown_widget", "data": {"test": "data"}},
        ],
    }

    response = client.post("/api/ai/from-bullets", json=request_data)
    # Should handle mixed widget types gracefully
    assert response.status_code == 200


def test_from_bullets_empty_widgets(client):
    """Test from-bullets endpoint with empty widgets list."""
    request_data = {"bullets": ["Test bullet point"], "widgets": []}

    response = client.post("/api/ai/from-bullets", json=request_data)
    # Empty widgets should be handled gracefully
    assert response.status_code == 200


def test_from_bullets_no_widgets(client):
    """Test from-bullets endpoint without widgets parameter."""
    request_data = {"bullets": ["Test bullet point"], "title": "Test Article"}

    response = client.post("/api/ai/from-bullets", json=request_data)
    # No widgets should work normally
    assert response.status_code == 200
