# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install with dev dependencies
uv sync --dev

# Install MCP server for Claude Code
claude mcp add openrouter --scope user -- uv run --directory /path/to/mcp-openrouter mcp-openrouter

# Run the server (requires API key)
OPENROUTER_API_KEY=your-key uv run mcp-openrouter

# Run tests (requires API key for integration tests)
OPENROUTER_API_KEY=your-key uv run pytest tests/

# Run a single test
OPENROUTER_API_KEY=your-key uv run pytest tests/test_tools.py::TestChatTool::test_chat_returns_string -v

# Lint with ruff
uv run ruff check src/
uv run ruff format src/
```

## Configuration

Environment variables (set in `.env` file or shell):

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | **Required.** Your OpenRouter API key |
| `DEFAULT_TEXT_MODEL` | Default model for `chat` tool (e.g., `anthropic/claude-sonnet-4`) |
| `DEFAULT_IMAGE_MODEL` | Default model for `generate_image` tool (e.g., `google/gemini-3-pro-image-preview`) |
| `DEFAULT_CODE_MODEL` | Default model for code-related tasks |
| `DEFAULT_VISION_MODEL` | Default model for vision tasks |

When default models are configured, the `model` parameter becomes optional in tool calls.

## Architecture

This is an MCP (Model Context Protocol) server built with FastMCP that exposes OpenRouter's API as tools.

**Key components:**
- `src/openrouter_mcp/server.py` - MCP server with tool definitions (`chat`, `generate_image`, `list_models`, `find_models`)
- `src/openrouter_mcp/client.py` - `OpenRouterClient` class handling API requests with retry logic
- `src/openrouter_mcp/config.py` - Configuration management for default models

**Flow:** MCP tools in `server.py` → `get_client()` → `OpenRouterClient` methods → OpenRouter API

**Entry point:** `mcp-openrouter` CLI command runs `server:main()` which starts the FastMCP server.

## Project Guidelines

- README.md must be kept up to date with any significant project changes
- Tests require `OPENROUTER_API_KEY` environment variable (tests are skipped if not set)
- Python 3.10+ required
