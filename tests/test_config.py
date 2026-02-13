"""Unit tests for config module."""

import os
from unittest.mock import patch

from mcp_openrouter.config import get_default_model


class TestGetDefaultModel:
    def test_text(self):
        with patch.dict(os.environ, {"DEFAULT_TEXT_MODEL": "anthropic/claude-sonnet-4"}):
            assert get_default_model("text") == "anthropic/claude-sonnet-4"

    def test_image(self):
        with patch.dict(os.environ, {"DEFAULT_IMAGE_MODEL": "some/model"}):
            assert get_default_model("image") == "some/model"

    def test_code(self):
        with patch.dict(os.environ, {"DEFAULT_CODE_MODEL": "code/model"}):
            assert get_default_model("code") == "code/model"

    def test_vision(self):
        with patch.dict(os.environ, {"DEFAULT_VISION_MODEL": "vision/model"}):
            assert get_default_model("vision") == "vision/model"

    def test_embedding(self):
        with patch.dict(os.environ, {"DEFAULT_EMBEDDING_MODEL": "embed/model"}):
            assert get_default_model("embedding") == "embed/model"

    def test_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_default_model("text") is None

    def test_unknown_category(self):
        assert get_default_model("unknown") is None
