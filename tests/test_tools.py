"""Tests for OpenRouter MCP tools."""

import os
from unittest.mock import MagicMock, patch

import pytest


# Skip all tests if no API key is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


class TestChatTool:
    """Tests for the chat tool."""

    def test_chat_returns_string(self):
        """Chat should return a string response."""
        from openrouter_mcp.server import chat

        # Use a fast, cheap model for testing
        result = chat(
            model="openai/gpt-4o-mini",
            prompt="Say 'test' and nothing else.",
            max_tokens=10,
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestListModelsTool:
    """Tests for the list_models tool."""

    def test_list_models_returns_list(self):
        """list_models should return a list of model dicts."""
        from openrouter_mcp.server import list_models

        result = list_models()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "slug" in result[0]
        assert "name" in result[0]

    def test_list_models_with_capability_filter(self):
        """list_models should filter by capability."""
        from openrouter_mcp.server import list_models

        result = list_models(capability="image_gen")
        assert isinstance(result, list)
        # Should have fewer results than unfiltered
        all_models = list_models()
        assert len(result) < len(all_models)


class TestFindModelsTool:
    """Tests for the find_models tool."""

    def test_find_models_returns_matches(self):
        """find_models should return matching models."""
        from openrouter_mcp.server import find_models

        result = find_models("claude")
        assert isinstance(result, list)
        assert len(result) > 0
        # All results should contain "claude" in slug or name
        for model in result:
            assert (
                "claude" in model["slug"].lower()
                or "claude" in model["name"].lower()
            )

    def test_find_models_limits_results(self):
        """find_models should return at most 20 results."""
        from openrouter_mcp.server import find_models

        result = find_models("a")  # Very broad search
        assert len(result) <= 20
