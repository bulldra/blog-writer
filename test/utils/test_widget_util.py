"""Tests for widget utility functions."""

from app.widget_util import (
    get_widget_default_config,
    validate_widget_config,
    process_widget_sync,
)


def test_get_widget_default_config():
    """Test getting default configuration for widgets."""
    notion_config = get_widget_default_config("notion")

    assert notion_config["page_ids"] == []
    assert notion_config["search_query"] == ""
    assert notion_config["max_pages"] == 5

    # Test unknown widget type
    unknown_config = get_widget_default_config("unknown_widget")
    assert unknown_config == {}


def test_validate_widget_config_notion():
    """Test validation of Notion widget configuration."""
    # Valid config with page IDs
    valid_config1 = {
        "page_ids": ["page_id_1", "page_id_2"],
        "search_query": "",
        "max_pages": 5,
    }
    assert validate_widget_config("notion", valid_config1) is True

    # Valid config with search query
    valid_config2 = {"page_ids": [], "search_query": "test query", "max_pages": 3}
    assert validate_widget_config("notion", valid_config2) is True

    # Valid config with both
    valid_config3 = {
        "page_ids": ["page_id_1"],
        "search_query": "test query",
        "max_pages": 1,
    }
    assert validate_widget_config("notion", valid_config3) is True

    # Invalid: no page IDs and no search query
    invalid_config1 = {"page_ids": [], "search_query": "", "max_pages": 5}
    assert validate_widget_config("notion", invalid_config1) is False

    # Invalid: page_ids is not a list
    invalid_config2 = {"page_ids": "not_a_list", "search_query": "", "max_pages": 5}
    assert validate_widget_config("notion", invalid_config2) is False

    # Invalid: empty page ID in list
    invalid_config3 = {"page_ids": ["valid_id", ""], "search_query": "", "max_pages": 5}
    assert validate_widget_config("notion", invalid_config3) is False

    # Invalid: search_query is not a string
    invalid_config4 = {"page_ids": [], "search_query": 123, "max_pages": 5}
    assert validate_widget_config("notion", invalid_config4) is False


def test_validate_widget_config_unknown():
    """Test validation for unknown widget types."""
    # Unknown widget types always return True
    assert validate_widget_config("unknown_type", {}) is True
    assert validate_widget_config("another_unknown", {"any": "data"}) is True


def test_process_widget_sync_notion_disabled():
    """Test processing Notion widget when disabled."""
    # This test verifies that the function handles disabled Notion gracefully
    widget_data = {"page_ids": ["test_page_id"], "search_query": "", "max_pages": 1}

    # Should return None when Notion is disabled or not configured
    result = process_widget_sync("notion", widget_data)
    # We expect None since Notion is not configured in test environment
    assert result is None


def test_process_widget_sync_unknown_type():
    """Test processing unknown widget type."""
    result = process_widget_sync("unknown_type", {})
    assert result is None


def test_process_widget_sync_empty_data():
    """Test processing with empty widget data."""
    result = process_widget_sync("notion", {})
    # Should return None due to validation failure (no page_ids or search_query)
    assert result is None


def test_process_widget_sync_invalid_data():
    """Test processing with invalid widget data."""
    invalid_data = {
        "page_ids": [],
        "search_query": "",  # Both empty, should fail validation
        "max_pages": 5,
    }

    result = process_widget_sync("notion", invalid_data)
    assert result is None
