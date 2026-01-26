"""OpenRouter MCP Server.

Exposes OpenRouter API capabilities as MCP tools for text completion,
image generation, and model discovery.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from the package directory (where the repo is cloned)
_package_dir = Path(__file__).parent.parent.parent
load_dotenv(_package_dir / ".env")

from openrouter_mcp.client import OpenRouterClient
from openrouter_mcp.config import get_default_model

# Initialize FastMCP server
mcp = FastMCP(
    "openrouter",
    instructions="""OpenRouter MCP Server provides access to 300+ AI models.

Available tools:
- chat: Text completion with any model
- generate_image: Image generation with image models
- list_models: List available models by capability
- find_models: Search for models by name

Requires OPENROUTER_API_KEY environment variable.""",
)


def get_client() -> OpenRouterClient:
    """Get an initialized OpenRouter client."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable not set. "
            "Get your key at: https://openrouter.ai/keys"
        )
    return OpenRouterClient(api_key)


@mcp.tool()
def chat(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    json_mode: bool = False,
) -> str:
    """Send a chat completion request to any OpenRouter model.

    Args:
        prompt: User message to send
        model: Model identifier (e.g., "anthropic/claude-sonnet-4", "openai/gpt-4o").
            If not specified, uses DEFAULT_TEXT_MODEL environment variable.
        system: Optional system prompt to set context
        max_tokens: Maximum tokens in response (model default if not specified)
        temperature: Sampling temperature 0-2 (model default if not specified)
        json_mode: If True, request JSON-formatted response

    Returns:
        The model's response text
    """
    resolved_model = model or get_default_model("text")
    if not resolved_model:
        raise ValueError(
            "No model specified. Either pass the 'model' parameter or set "
            "DEFAULT_TEXT_MODEL environment variable."
        )

    client = get_client()

    kwargs = {}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    return client.chat_simple(resolved_model, prompt, system=system, **kwargs)


@mcp.tool()
def generate_image(
    prompt: str,
    output_path: str,
    model: Optional[str] = None,
    aspect_ratio: str = "1:1",
    size: str = "1K",
    background: Optional[str] = None,
    quality: Optional[str] = None,
    output_format: Optional[str] = None,
) -> str:
    """Generate an image using an OpenRouter image generation model.

    Args:
        prompt: Image description - be specific about style, colors, composition
        output_path: Absolute path to save the image (e.g., "/path/to/image.png")
        model: Image model (e.g., "google/gemini-3-pro-image-preview").
            If not specified, uses DEFAULT_IMAGE_MODEL environment variable.
        aspect_ratio: Aspect ratio - 1:1, 16:9, 9:16, 4:3, 3:4, or 21:9
        size: Image size - 1K, 2K, or 4K
        background: Background setting (e.g., "transparent" for PNG/WebP)
        quality: Quality setting (e.g., "high", "medium", "low")
        output_format: Output format (e.g., "png", "webp", "jpeg")

    Returns:
        Success message with the saved file path
    """
    resolved_model = model or get_default_model("image")
    if not resolved_model:
        raise ValueError(
            "No model specified. Either pass the 'model' parameter or set "
            "DEFAULT_IMAGE_MODEL environment variable."
        )

    client = get_client()

    images = client.generate_image(
        resolved_model,
        prompt,
        output_path,
        aspect_ratio=aspect_ratio,
        size=size,
        background=background,
        quality=quality,
        output_format=output_format,
    )

    if images:
        return f"Generated image saved to {output_path}"
    else:
        return "No image was generated. Try adjusting the prompt or model."


@mcp.tool()
def list_models(capability: Optional[str] = None) -> list[dict]:
    """List available OpenRouter models, optionally filtered by capability.

    Args:
        capability: Filter by capability:
            - "vision": Models that can analyze images
            - "image_gen": Models that can generate images
            - "tools": Models that support tool/function calling
            - "long_context": Models with 100k+ context window

    Returns:
        List of models with slug, name, context_length, and pricing info
    """
    client = get_client()
    models = client.list_models(capability)

    # Return simplified model info
    return [
        {
            "slug": m["slug"],
            "name": m["name"],
            "context_length": m.get("context_length"),
            "pricing": {
                "prompt": m.get("pricing", {}).get("prompt"),
                "completion": m.get("pricing", {}).get("completion"),
            },
        }
        for m in models
    ]


@mcp.tool()
def find_models(search_term: str) -> list[dict]:
    """Search for models by name or slug.

    Args:
        search_term: Text to search for in model names (e.g., "claude", "gpt", "gemini")

    Returns:
        List of matching models (max 20) with slug, name, and context_length
    """
    client = get_client()
    matches = client.find_model(search_term)

    # Return simplified model info, limited to 20 results
    return [
        {
            "slug": m["slug"],
            "name": m["name"],
            "context_length": m.get("context_length"),
        }
        for m in matches[:20]
    ]


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
