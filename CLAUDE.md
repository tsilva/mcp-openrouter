# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in development mode
pip install -e .

# Run the server (requires API key)
OPENROUTER_API_KEY=your-key openrouter-mcp

# Run tests (requires API key for integration tests)
OPENROUTER_API_KEY=your-key pytest tests/

# Run a single test
OPENROUTER_API_KEY=your-key pytest tests/test_tools.py::TestChatTool::test_chat_returns_string -v

# Lint with ruff
ruff check src/
ruff format src/
```

## Architecture

This is an MCP (Model Context Protocol) server built with FastMCP that exposes OpenRouter's API as tools.

**Key components:**
- `src/openrouter_mcp/server.py` - MCP server with tool definitions (`chat`, `generate_image`, `list_models`, `find_models`)
- `src/openrouter_mcp/client.py` - `OpenRouterClient` class handling API requests with retry logic

**Flow:** MCP tools in `server.py` → `get_client()` → `OpenRouterClient` methods → OpenRouter API

**Entry point:** `openrouter-mcp` CLI command runs `server:main()` which starts the FastMCP server.

## Project Guidelines

- README.md must be kept up to date with any significant project changes
- Tests require `OPENROUTER_API_KEY` environment variable (tests are skipped if not set)
- Python 3.10+ required
