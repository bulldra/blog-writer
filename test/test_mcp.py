"""Test MCP functionality."""

from app.storage import (
    add_mcp_server,
    get_mcp_settings,
    remove_mcp_server,
    save_mcp_settings,
)
from app.widget_util import get_widget_default_config, validate_widget_config


class TestMCPStorage:
    """Test MCP storage functionality."""

    def test_get_default_mcp_config(self):
        """Test getting default MCP configuration."""
        config = get_widget_default_config("mcp")
        expected = {
            "server_id": "",
            "tool_name": "",
            "arguments": {},
        }
        assert config == expected

    def test_validate_mcp_widget_config_valid(self):
        """Test validating valid MCP widget configuration."""
        config = {
            "server_id": "test-server",
            "tool_name": "test-tool",
            "arguments": {"key": "value"},
        }
        assert validate_widget_config("mcp", config) is True

    def test_validate_mcp_widget_config_missing_server_id(self):
        """Test validating MCP widget configuration with missing server_id."""
        config = {
            "server_id": "",
            "tool_name": "test-tool",
            "arguments": {},
        }
        assert validate_widget_config("mcp", config) is False

    def test_validate_mcp_widget_config_missing_tool_name(self):
        """Test validating MCP widget configuration with missing tool_name."""
        config = {
            "server_id": "test-server",
            "tool_name": "",
            "arguments": {},
        }
        assert validate_widget_config("mcp", config) is False

    def test_validate_mcp_widget_config_invalid_arguments(self):
        """Test validating MCP widget configuration with invalid arguments."""
        config = {
            "server_id": "test-server",
            "tool_name": "test-tool",
            "arguments": "not-a-dict",
        }
        assert validate_widget_config("mcp", config) is False

    def test_mcp_settings_crud(self):
        """Test MCP settings CRUD operations."""
        # Clean up any existing test data first
        try:
            remove_mcp_server("test-server")
        except Exception:
            pass  # Ignore if server doesn't exist

        # Get initial settings
        get_mcp_settings()

        # Add a server
        add_mcp_server(
            server_id="test-server",
            name="Test Server",
            command="npx",
            args=["@test/mcp-server"],
            env={"TEST_API_KEY": "secret"},
            enabled=True,
        )

        # Check it was added
        settings = get_mcp_settings()
        assert "test-server" in settings["servers"]
        server = settings["servers"]["test-server"]
        assert server["name"] == "Test Server"
        assert server["command"] == "npx"
        assert server["args"] == ["@test/mcp-server"]
        assert server["env"] == {"TEST_API_KEY": "secret"}
        assert server["enabled"] is True

        # Update global settings
        save_mcp_settings(servers=settings["servers"], enabled=True)
        updated_settings = get_mcp_settings()
        assert updated_settings["enabled"] is True

        # Remove the server
        removed = remove_mcp_server("test-server")
        assert removed is True

        # Check it was removed
        settings = get_mcp_settings()
        assert "test-server" not in settings["servers"]

        # Try to remove non-existent server
        removed = remove_mcp_server("non-existent")
        assert removed is False
