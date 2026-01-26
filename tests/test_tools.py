"""Tests for OpenRouter MCP tools."""

import os

import pytest

# Skip all tests if no API key is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


class TestModelDefaults:
    """Tests for configurable model defaults."""

    def test_chat_uses_default_model(self, monkeypatch):
        """Chat should use default model when none specified."""
        from mcp_openrouter.server import chat

        monkeypatch.setenv("DEFAULT_TEXT_MODEL", "openai/gpt-4o-mini")

        result = chat(prompt="Say 'test' and nothing else.", max_tokens=10)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chat_raises_error_without_model_or_default(self, monkeypatch):
        """Chat should raise error when no model and no default configured."""
        from mcp_openrouter.server import chat

        monkeypatch.delenv("DEFAULT_TEXT_MODEL", raising=False)

        with pytest.raises(ValueError) as exc_info:
            chat(prompt="Test")

        assert "DEFAULT_TEXT_MODEL" in str(exc_info.value)

    def test_chat_explicit_model_overrides_default(self, monkeypatch):
        """Explicit model parameter should override the default."""
        from mcp_openrouter.server import chat

        # Set a default that we won't use
        monkeypatch.setenv("DEFAULT_TEXT_MODEL", "some/other-model")

        # Explicitly specify a different model
        result = chat(
            model="openai/gpt-4o-mini",
            prompt="Say 'test' and nothing else.",
            max_tokens=10,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_image_raises_error_without_model_or_default(self, monkeypatch):
        """generate_image should raise error when no model and no default configured."""
        from mcp_openrouter.server import generate_image

        monkeypatch.delenv("DEFAULT_IMAGE_MODEL", raising=False)

        with pytest.raises(ValueError) as exc_info:
            generate_image(prompt="A test image", output_path="/tmp/test.png")

        assert "DEFAULT_IMAGE_MODEL" in str(exc_info.value)


class TestChatTool:
    """Tests for the chat tool."""

    def test_chat_returns_string(self):
        """Chat should return a string response."""
        from mcp_openrouter.server import chat

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
        from mcp_openrouter.server import list_models

        result = list_models()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "slug" in result[0]
        assert "name" in result[0]

    def test_list_models_with_capability_filter(self):
        """list_models should filter by capability."""
        from mcp_openrouter.server import list_models

        result = list_models(capability="image_gen")
        assert isinstance(result, list)
        # Should have fewer results than unfiltered
        all_models = list_models()
        assert len(result) < len(all_models)


class TestFindModelsTool:
    """Tests for the find_models tool."""

    def test_find_models_returns_matches(self):
        """find_models should return matching models."""
        from mcp_openrouter.server import find_models

        result = find_models("claude")
        assert isinstance(result, list)
        assert len(result) > 0
        # All results should contain "claude" in slug or name
        for model in result:
            assert (
                "claude" in model["slug"].lower() or "claude" in model["name"].lower()
            )

    def test_find_models_limits_results(self):
        """find_models should return at most 20 results."""
        from mcp_openrouter.server import find_models

        result = find_models("a")  # Very broad search
        assert len(result) <= 20
