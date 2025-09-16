"""Tests for Notion MCP integration."""

import pytest
from app.notion_util import get_default_notion_config, format_notion_page_for_context
from app.storage import save_notion_settings, get_notion_settings


def test_default_notion_config():
    """Test getting default Notion configuration."""
    config = get_default_notion_config()
    
    assert config["command"] == "npx"
    assert config["args"] == ["@modelcontextprotocol/server-notion"]
    assert "NOTION_API_KEY" in config["env"]
    assert config["enabled"] is False


def test_notion_settings_storage():
    """Test storing and retrieving Notion settings."""
    # Save test settings
    save_notion_settings(
        command="npx",
        args=["@modelcontextprotocol/server-notion"],
        env={"NOTION_API_KEY": "test_key"},
        enabled=True,
        default_parent_id="test_parent_id"
    )
    
    # Retrieve settings
    settings = get_notion_settings()
    
    assert settings["command"] == "npx"
    assert settings["args"] == ["@modelcontextprotocol/server-notion"]
    assert settings["env"]["NOTION_API_KEY"] == "test_key"
    assert settings["enabled"] is True
    assert settings["default_parent_id"] == "test_parent_id"


def test_format_notion_page_for_context():
    """Test formatting Notion page data for context."""
    # Mock page data
    page_data = {
        "properties": {
            "title": {
                "title": [{"plain_text": "Test Page Title"}]
            },
            "status": {
                "type": "select",
                "select": {"name": "Published"}
            },
            "tags": {
                "type": "multi_select",
                "multi_select": [
                    {"name": "tag1"},
                    {"name": "tag2"}
                ]
            },
            "created_date": {
                "type": "date",
                "date": {"start": "2024-01-01"}
            }
        },
        "content": "This is the page content."
    }
    
    result = format_notion_page_for_context(page_data)
    
    assert "## Test Page Title" in result
    assert "### プロパティ" in result
    assert "status: Published" in result
    assert "tags: tag1, tag2" in result
    assert "created_date: 2024-01-01" in result
    assert "### コンテンツ" in result
    assert "This is the page content." in result


def test_format_notion_page_minimal():
    """Test formatting minimal Notion page data."""
    # Minimal page data
    page_data = {
        "properties": {}
    }
    
    result = format_notion_page_for_context(page_data)
    
    assert "## Untitled" in result
    assert "### プロパティ" not in result
    assert "### コンテンツ" not in result


def test_format_notion_page_with_rich_text():
    """Test formatting page with rich text properties."""
    page_data = {
        "properties": {
            "title": {
                "title": [{"plain_text": "Rich Text Test"}]
            },
            "description": {
                "type": "rich_text",
                "rich_text": [
                    {"plain_text": "First part "},
                    {"plain_text": "second part"}
                ]
            }
        }
    }
    
    result = format_notion_page_for_context(page_data)
    
    assert "## Rich Text Test" in result
    assert "description: First part  second part" in result


def test_format_notion_page_empty_properties():
    """Test formatting page with empty properties that should be filtered."""
    page_data = {
        "properties": {
            "title": {
                "title": [{"plain_text": "Filter Test"}]
            },
            "empty_select": {
                "type": "select",
                "select": None
            },
            "empty_rich_text": {
                "type": "rich_text", 
                "rich_text": []
            },
            "valid_text": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "Valid content"}]
            }
        }
    }
    
    result = format_notion_page_for_context(page_data)
    
    assert "## Filter Test" in result
    assert "valid_text: Valid content" in result
    assert "empty_select:" not in result
    assert "empty_rich_text:" not in result