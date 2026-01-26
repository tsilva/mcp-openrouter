"""Configuration management for OpenRouter MCP Server."""

import os
from typing import Optional

MODEL_DEFAULTS = {
    "text": "DEFAULT_TEXT_MODEL",
    "image": "DEFAULT_IMAGE_MODEL",
    "code": "DEFAULT_CODE_MODEL",
    "vision": "DEFAULT_VISION_MODEL",
}


def get_default_model(category: str) -> Optional[str]:
    """Get the default model for a given category.

    Args:
        category: Model category ("text", "image", "code", "vision")

    Returns:
        The configured default model identifier, or None if not set.
    """
    env_var = MODEL_DEFAULTS.get(category)
    if not env_var:
        return None
    return os.environ.get(env_var)
