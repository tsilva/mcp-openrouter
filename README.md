<div align="center">
  <img src="logo.png" alt="mcp-openrouter" width="512">

  # mcp-openrouter

  [![Python](https://img.shields.io/pypi/pyversions/mcp-openrouter)](https://pypi.org/project/mcp-openrouter/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

  **🚀 Access 300+ AI models through a single MCP server — text, images, embeddings, and model discovery at your fingertips 🤖**

</div>

## Overview

[![CI](https://github.com/tsilva/mcp-openrouter/actions/workflows/release.yml/badge.svg)](https://github.com/tsilva/mcp-openrouter/actions/workflows/release.yml)

mcp-openrouter is an MCP (Model Context Protocol) server that provides seamless access to OpenRouter's extensive catalog of AI models. Use Claude, GPT, Gemini, Llama, and 300+ other models through a unified interface.

## Features

- ✨ **Text Completion** — Chat with any OpenRouter model (Claude, GPT, Gemini, Mistral, etc.)
- 🎨 **Image Generation** — Create images with DALL-E, Gemini, and other image models
- 📐 **Embeddings** — Generate vector embeddings with Mistral, OpenAI, Gemini, and other embedding models
- 🔍 **Model Discovery** — List and search 300+ models by capability
- ⚡ **Persistent Connection** — No repeated setup or permission prompts
- 🔧 **Zero Config** — Just set your API key and go

## Quick Start

### Installation

```bash
uv pip install mcp-openrouter
```

Or run directly with uvx:

```bash
uvx mcp-openrouter
```

### Configuration

#### Claude Code

1. Clone the repository:
   ```bash
   git clone https://github.com/tsilva/mcp-openrouter.git
   cd mcp-openrouter
   ```

2. Create your `.env` file with your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your key from https://openrouter.ai/keys
   ```

3. Add the MCP server:
   ```bash
   claude mcp add openrouter --scope user -- uv run --directory /path/to/mcp-openrouter mcp-openrouter
   ```

4. Restart Claude Code

5. Verify installation:
   ```bash
   claude mcp list
   # Should show: openrouter: ... - ✓ Connected
   ```

To uninstall:

```bash
claude mcp remove openrouter --scope user
```

#### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "uv",
      "args": ["run", "mcp-openrouter"],
      "cwd": "/path/to/mcp-openrouter"
    }
  }
}
```

Then create a `.env` file in the `mcp-openrouter` directory with your API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get your API key at [openrouter.ai/keys](https://openrouter.ai/keys).

### Default Models

Configure default models for different use cases. When set, the `model` parameter becomes optional in tool calls:

```bash
# Add to your .env file
DEFAULT_TEXT_MODEL=anthropic/claude-sonnet-4
DEFAULT_IMAGE_MODEL=google/gemini-3-pro-image-preview
DEFAULT_CODE_MODEL=anthropic/claude-sonnet-4
DEFAULT_VISION_MODEL=anthropic/claude-sonnet-4
DEFAULT_EMBEDDING_MODEL=mistralai/mistral-embed-2312
```

These are included in `.env.example` — copy it to `.env` and adjust as needed.

## Tools

| Tool | Description |
|------|-------------|
| `chat` | Send chat completion requests to any model |
| `generate_image` | Generate images with image models |
| `embed` | Generate vector embeddings for text |
| `list_models` | List available models, filter by capability |
| `find_models` | Search for models by name |

### Examples

**Chat with any model:**
```
Use openrouter chat with anthropic/claude-sonnet-4 to explain quantum computing
```

**Generate an image:**
```
Use openrouter generate_image with google/gemini-3-pro-image-preview to create a logo for my app
```

**Find models:**
```
Use openrouter find_models to search for "claude"
```

**Generate embeddings:**
```
Use openrouter embed with mistralai/mistral-embed-2312 to embed "Hello world"
```

**List image generation models:**
```
Use openrouter list_models with capability "image_gen"
```

## API Reference

### chat

Send a chat completion request to any OpenRouter model.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | User message to send |
| `model` | string | No* | Model identifier (e.g., `anthropic/claude-sonnet-4`) |
| `system` | string | No | System prompt for context |
| `max_tokens` | int | No | Maximum tokens in response |
| `temperature` | float | No | Sampling temperature (0-2) |
| `json_mode` | bool | No | Request JSON-formatted response |

*Required unless `DEFAULT_TEXT_MODEL` is set.

### generate_image

Generate an image using an OpenRouter image model.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Image description |
| `output_path` | string | Yes | Absolute path to save the image |
| `model` | string | No* | Image model (e.g., `google/gemini-3-pro-image-preview`) |
| `aspect_ratio` | string | No | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9` |
| `size` | string | No | `1K`, `2K`, or `4K` |
| `background` | string | No | Background setting (e.g., `transparent`) |

*Required unless `DEFAULT_IMAGE_MODEL` is set.

### embed

Generate vector embeddings for text input.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | string or list | Yes | Text string or list of strings to embed |
| `model` | string | No* | Embedding model (e.g., `mistralai/mistral-embed-2312`) |
| `encoding_format` | string | No | Output format: `float` or `base64` |
| `dimensions` | int | No | Custom embedding dimensions (model-dependent) |

*Required unless `DEFAULT_EMBEDDING_MODEL` is set.

### list_models

List available models, optionally filtered by capability.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `capability` | string | No | Filter: `vision`, `image_gen`, `embedding`, `tools`, `long_context` |

### find_models

Search for models by name or slug.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_term` | string | Yes | Text to search in model names |

## Development

```bash
# Clone the repository
git clone https://github.com/tsilva/mcp-openrouter.git
cd mcp-openrouter

# Install dependencies
uv sync --dev

# Run the server
OPENROUTER_API_KEY=your-key uv run mcp-openrouter

# Run tests
OPENROUTER_API_KEY=your-key uv run pytest tests/

# Lint
uv run ruff check src/
uv run ruff format src/
```

### Applying Code Changes

When you modify the MCP server code, Claude won't automatically pick up the changes. The server runs as a long-lived process that persists across tool calls within a session.

**To apply your changes:**

1. **Start a new Claude Code session** — Close your current terminal/conversation and open a new one. The MCP server process restarts when a new session begins.

2. **Or use the `/mcp` command** — Check server status and restart options within Claude Code.

**Why this works:** The installation uses `uv run --directory /path/to/mcp-openrouter` which executes code directly from your source directory. There's no separate "install" step needed — just restart the server process to load your changes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT](LICENSE)
