"""Tests for Notion API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_get_notion_settings(client):
    """Test getting Notion settings."""
    response = client.get("/api/notion/settings")
    assert response.status_code == 200
    
    data = response.json()
    assert "command" in data
    assert "args" in data
    assert "env" in data
    assert "enabled" in data
    assert "default_parent_id" in data


def test_save_notion_settings(client):
    """Test saving Notion settings."""
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": "test_key"},
        "enabled": True,
        "default_parent_id": "test_parent"
    }
    
    response = client.post("/api/notion/settings", json=settings_data)
    assert response.status_code == 200
    assert response.json() == {"status": "saved"}
    
    # Verify settings were saved
    get_response = client.get("/api/notion/settings")
    assert get_response.status_code == 200
    saved_data = get_response.json()
    assert saved_data["command"] == "npx"
    assert saved_data["enabled"] is True
    assert saved_data["default_parent_id"] == "test_parent"


def test_test_connection_disabled(client):
    """Test connection test when Notion is disabled."""
    # First disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    response = client.post("/api/notion/test-connection")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert "disabled" in data["error"]


def test_test_connection_no_api_key(client):
    """Test connection test when API key is missing."""
    # Enable Notion but don't provide API key
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": True,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    response = client.post("/api/notion/test-connection")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert "API key" in data["error"]


def test_list_pages_disabled(client):
    """Test listing pages when Notion is disabled."""
    # Disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    response = client.get("/api/notion/pages")
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_search_pages_disabled(client):
    """Test searching pages when Notion is disabled."""
    # Disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    search_data = {"query": "test", "limit": 10}
    response = client.post("/api/notion/search", json=search_data)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_create_page_disabled(client):
    """Test creating page when Notion is disabled."""
    # Disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    page_data = {
        "title": "Test Page",
        "content": "Test content",
        "parent_id": None
    }
    response = client.post("/api/notion/create-page", json=page_data)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_get_page_context_disabled(client):
    """Test getting page context when Notion is disabled."""
    # Disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    response = client.get("/api/notion/pages/test_page_id/context")
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_search_pages_validation(client):
    """Test search request validation."""
    # Enable Notion with API key for validation test
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": "test_key"},
        "enabled": True,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    # Test with invalid limit
    search_data = {"query": "test", "limit": 100}  # limit too high
    response = client.post("/api/notion/search", json=search_data)
    # This should pass validation but fail on connection
    # We're not testing actual connection, just API structure
    assert response.status_code in [400, 422, 500]  # Various failure modes acceptable
    
    # Test with missing query
    search_data = {"limit": 10}
    response = client.post("/api/notion/search", json=search_data)
    assert response.status_code == 422  # Validation error


def test_publish_article_disabled(client):
    """Test publishing article when Notion is disabled."""
    # Disable Notion
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": ""},
        "enabled": False,
        "default_parent_id": ""
    }
    client.post("/api/notion/settings", json=settings_data)
    
    article_data = {
        "title": "Test Article",
        "content": "# Test Article\n\nThis is a test article content.",
        "parent_id": None
    }
    response = client.post("/api/notion/publish-article", json=article_data)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_publish_article_validation(client):
    """Test publish article request validation."""
    # Enable Notion with API key
    settings_data = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-notion"],
        "env": {"NOTION_API_KEY": "test_key"},
        "enabled": True,
        "default_parent_id": "default_parent"
    }
    client.post("/api/notion/settings", json=settings_data)
    
    # Test with missing title
    article_data = {
        "content": "Test content"
    }
    response = client.post("/api/notion/publish-article", json=article_data)
    assert response.status_code == 422  # Validation error
    
    # Test with missing content
    article_data = {
        "title": "Test Title"
    }
    response = client.post("/api/notion/publish-article", json=article_data)
    assert response.status_code == 422  # Validation error