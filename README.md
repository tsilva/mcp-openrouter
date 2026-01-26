<div align="center">
  <img src="logo.png" alt="mcp-openrouter" width="512"/>

  # mcp-openrouter

  [![PyPI](https://img.shields.io/pypi/v/openrouter-mcp)](https://pypi.org/project/openrouter-mcp/)
  [![Python](https://img.shields.io/pypi/pyversions/openrouter-mcp)](https://pypi.org/project/openrouter-mcp/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

  **🚀 Access 300+ AI models through a single MCP server — text, images, and model discovery at your fingertips**

</div>

## Overview

mcp-openrouter is an MCP (Model Context Protocol) server that provides seamless access to OpenRouter's extensive catalog of AI models. Use Claude, GPT, Gemini, Llama, and 300+ other models through a unified interface.

## Features

- ✨ **Text Completion** — Chat with any OpenRouter model (Claude, GPT, Gemini, Mistral, etc.)
- 🎨 **Image Generation** — Create images with DALL-E, Gemini, and other image models
- 🔍 **Model Discovery** — List and search 300+ models by capability
- ⚡ **Persistent Connection** — No repeated setup or permission prompts
- 🔧 **Zero Config** — Just set your API key and go

## Quick Start

### Installation

```bash
pip install openrouter-mcp
```

Or with uvx:

```bash
uvx openrouter-mcp
```

### Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "openrouter-mcp",
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-your-key-here"
      }
    }
  }
}
```

Get your API key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Tools

| Tool | Description |
|------|-------------|
| `chat` | Send chat completion requests to any model |
| `generate_image` | Generate images with image models |
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

**List image generation models:**
```
Use openrouter list_models with capability "image_gen"
```

## API Reference

### chat

Send a chat completion request to any OpenRouter model.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model identifier (e.g., `anthropic/claude-sonnet-4`) |
| `prompt` | string | Yes | User message to send |
| `system` | string | No | System prompt for context |
| `max_tokens` | int | No | Maximum tokens in response |
| `temperature` | float | No | Sampling temperature (0-2) |
| `json_mode` | bool | No | Request JSON-formatted response |

### generate_image

Generate an image using an OpenRouter image model.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Image model (e.g., `google/gemini-3-pro-image-preview`) |
| `prompt` | string | Yes | Image description |
| `output_path` | string | Yes | Absolute path to save the image |
| `aspect_ratio` | string | No | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9` |
| `size` | string | No | `1K`, `2K`, or `4K` |
| `background` | string | No | Background setting (e.g., `transparent`) |

### list_models

List available models, optionally filtered by capability.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `capability` | string | No | Filter: `vision`, `image_gen`, `tools`, `long_context` |

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

# Install in development mode
pip install -e .

# Run the server
OPENROUTER_API_KEY=your-key openrouter-mcp
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT](LICENSE)
