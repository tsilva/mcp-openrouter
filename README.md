<div align="center">
  <img src="https://raw.githubusercontent.com/tsilva/mcp-openrouter/main/logo.png" alt="mcp-openrouter" width="512">

  # mcp-openrouter

  [![PyPI](https://img.shields.io/pypi/v/mcp-openrouter)](https://pypi.org/project/mcp-openrouter/)
  [![Python](https://img.shields.io/pypi/pyversions/mcp-openrouter)](https://pypi.org/project/mcp-openrouter/)
  [![CI](https://github.com/tsilva/mcp-openrouter/actions/workflows/release.yml/badge.svg)](https://github.com/tsilva/mcp-openrouter/actions/workflows/release.yml)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

  **🚀 One MCP server for OpenRouter models 🚀**

  [GitHub](https://github.com/tsilva/mcp-openrouter) · [PyPI](https://pypi.org/project/mcp-openrouter/) · [Issues](https://github.com/tsilva/mcp-openrouter/issues)
</div>

<!-- mcp-name: io.github.tsilva/mcp-openrouter -->

## Overview

### The Punchline

`mcp-openrouter` is a Python MCP server that gives Codex, Claude Code, opencode, and other MCP hosts access to OpenRouter's model catalog through five practical tools: chat, image generation, embeddings, model listing, and model search.

### The Pain

OpenRouter exposes hundreds of models, but every agent host needs a clean way to call them with the right API key, model defaults, request shape, and host-specific MCP configuration.

### The Solution

Install `mcp-openrouter` with `uvx`, persist your `OPENROUTER_API_KEY`, and let the server translate MCP tool calls into OpenRouter API requests with retry handling, `.env` support, and optional default models.

### The Result

You get one local stdio MCP server for text, images, embeddings, and model discovery across supported MCP clients, without wiring each workflow to OpenRouter manually.

| Fact | Detail |
|------|--------|
| MCP tools | `chat`, `generate_image`, `embed`, `list_models`, `find_models` |
| Supported installers | Codex, Claude Code, opencode |
| Runtime | Python 3.10+ with `uvx mcp-openrouter` |
| Registry package | `io.github.tsilva/mcp-openrouter` via PyPI package `mcp-openrouter` |

## Features

- **Unified chat requests**: send prompts or multi-turn message arrays to any OpenRouter chat model, with sampling, JSON response, reasoning, provider routing, and assistant prefill options.
- **Image generation**: create images through OpenRouter image-capable models, control aspect ratio and size, and optionally save generated files to an absolute local path.
- **Embeddings**: generate vector embeddings for a string or a list of strings, including optional encoding format and dimension controls.
- **Model discovery**: list OpenRouter models and filter by `vision`, `image_gen`, `embedding`, `tools`, or `long_context`.
- **Model search**: find matching model slugs by name or identifier and return a compact result set for fast selection.
- **Host-aware installer**: detect eligible MCP clients, prompt for targets, replace stale configs only when requested, and support non-interactive installs.
- **Default model configuration**: make `model` optional per tool by setting default model environment variables.
- **Retry and error handling**: retry transient OpenRouter failures and return clearer messages for authentication, credits, rate limits, and moderation errors.

## Quick Start

### Use It Now

Install into every detected MCP client:

```bash
uvx mcp-openrouter install --yes
```

Install into specific clients:

```bash
uvx mcp-openrouter install --yes --clients codex,claude
```

Pass the OpenRouter key directly for non-interactive setup:

```bash
uvx mcp-openrouter install --yes --api-key sk-or-v1-...
```

Replace an existing `openrouter` MCP config when it differs:

```bash
uvx mcp-openrouter install --yes --force
```

The interactive installer reuses `OPENROUTER_API_KEY` from your shell when it is set. Otherwise, it prompts securely.

### Run Locally

```bash
git clone https://github.com/tsilva/mcp-openrouter.git
cd mcp-openrouter
uv sync --dev
OPENROUTER_API_KEY=your-key uv run mcp-openrouter
```

`mcp-openrouter` with no arguments starts the stdio MCP server. The explicit equivalent is:

```bash
OPENROUTER_API_KEY=your-key uv run mcp-openrouter serve
```

### Check the Project

```bash
uv run pytest tests/test_cli.py tests/test_client.py tests/test_config.py tests/test_installer.py tests/test_release_metadata.py tests/test_server.py
OPENROUTER_API_KEY=your-key uv run pytest tests/test_tools.py
OPENROUTER_API_KEY=your-key uv run pytest tests/
uv run ruff check src/
uv run ruff format src/
```

Integration tests in `tests/test_tools.py` require a live OpenRouter API key. The unit tests mock network calls.

## Installation Details

The installer targets the production runtime command:

```bash
uvx mcp-openrouter
```

Installed host configs are equivalent to:

| Host | Configuration |
|------|---------------|
| Codex | `codex mcp add openrouter --env OPENROUTER_API_KEY=... -- uvx mcp-openrouter` |
| Claude Code | `claude mcp add -s user openrouter -e OPENROUTER_API_KEY=... -- uvx mcp-openrouter` |
| opencode | Adds `openrouter` under the `mcp` object in `~/.opencode/settings.json` |

Uninstall from all detected clients:

```bash
uvx mcp-openrouter uninstall --yes
```

Uninstall from selected clients:

```bash
uvx mcp-openrouter uninstall --yes --clients claude,opencode
```

Manual uninstall commands:

```bash
codex mcp remove openrouter
claude mcp remove -s user openrouter
```

For opencode, the uninstaller removes the `openrouter` entry from `~/.opencode/settings.json`.

## Configuration

Required:

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key used for all tool requests |

Optional defaults:

| Variable | Used by |
|----------|---------|
| `DEFAULT_TEXT_MODEL` | `chat` when no `model` is passed |
| `DEFAULT_IMAGE_MODEL` | `generate_image` when no `model` is passed |
| `DEFAULT_EMBEDDING_MODEL` | `embed` when no `model` is passed |
| `DEFAULT_CODE_MODEL` | Reserved for code-oriented client defaults |
| `DEFAULT_VISION_MODEL` | Reserved for vision-oriented client defaults |

The server loads environment variables from `.env` in the current working directory and from the repository root when running from a checkout.

Example `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_TEXT_MODEL=google/gemini-3-pro-image-preview
DEFAULT_IMAGE_MODEL=google/gemini-3-pro-image-preview
DEFAULT_CODE_MODEL=anthropic/claude-sonnet-4.5
DEFAULT_VISION_MODEL=google/gemini-3-pro-image-preview
DEFAULT_EMBEDDING_MODEL=mistralai/mistral-embed-2312
```

## Tool Usage

### Chat

```text
Use openrouter chat with anthropic/claude-sonnet-4 to summarize this file
```

`chat` accepts either `prompt` or `messages`, not both.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes* | User message to send |
| `messages` | array | Yes* | Multi-turn list of `{role, content}` messages |
| `model` | string | No** | OpenRouter model slug |
| `system` | string | No | System prompt prepended to the conversation |
| `max_tokens` | int | No | Maximum response tokens |
| `temperature` | float | No | Sampling temperature |
| `top_p` | float | No | Nucleus sampling threshold |
| `top_k` | int | No | Top-k sampling limit |
| `frequency_penalty` | float | No | Repetition penalty |
| `presence_penalty` | float | No | Presence penalty |
| `seed` | int | No | Deterministic seed when supported |
| `stop` | array | No | Stop sequences |
| `json_mode` | bool | No | Request JSON object output |
| `response_format` | object | No | Explicit OpenRouter response format |
| `reasoning_effort` | string | No | `minimal`, `medium`, or `high` |
| `provider` | object | No | Provider routing preferences |
| `assistant_prefill` | string | No | Assistant message prefix |

*Provide one of `prompt` or `messages`.

**Required unless `DEFAULT_TEXT_MODEL` is set.

### Generate Image

```text
Use openrouter generate_image with google/gemini-3-pro-image-preview to create a square app icon
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Image description |
| `model` | string | No* | OpenRouter image model slug |
| `aspect_ratio` | string | No | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, or `21:9` |
| `size` | string | No | `1K`, `2K`, or `4K` |
| `background` | string | No | Background setting such as `transparent` |
| `quality` | string | No | Quality setting such as `high`, `medium`, or `low` |
| `output_format` | string | No | `png`, `webp`, `jpeg`, or model-supported format |
| `output_path` | string | No | Absolute file path for saving the generated image |

*Required unless `DEFAULT_IMAGE_MODEL` is set.

### Embed

```text
Use openrouter embed with mistralai/mistral-embed-2312 to embed "Hello world"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | string or array | Yes | Text string or list of strings |
| `model` | string | No* | OpenRouter embedding model slug |
| `encoding_format` | string | No | `float` or `base64` |
| `dimensions` | int | No | Model-dependent output dimensions |

*Required unless `DEFAULT_EMBEDDING_MODEL` is set.

### List Models

```text
Use openrouter list_models with capability "image_gen"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `capability` | string | No | `vision`, `image_gen`, `embedding`, `tools`, or `long_context` |

### Find Models

```text
Use openrouter find_models to search for "claude"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_term` | string | Yes | Text to search for in model names or slugs |

## Architecture

```text
MCP host
  -> FastMCP tools in src/mcp_openrouter/server.py
  -> get_client()
  -> OpenRouterClient in src/mcp_openrouter/client.py
  -> https://openrouter.ai/api/v1
```

| Path | Purpose |
|------|---------|
| `src/mcp_openrouter/server.py` | FastMCP server, tool registration, env loading, tool argument validation |
| `src/mcp_openrouter/client.py` | OpenRouter HTTP client, retry handling, model normalization |
| `src/mcp_openrouter/config.py` | Default model environment variable lookup |
| `src/mcp_openrouter/cli.py` | `serve`, `install`, and `uninstall` command dispatch |
| `src/mcp_openrouter/installer.py` | MCP client detection and host-specific config writers |
| `server.json` | MCP Registry metadata for the PyPI package |
| `tests/` | Unit tests plus live OpenRouter integration tests |

## Local MCP Development

If you want an MCP host to run directly from a local checkout instead of the published PyPI package, register the repo path manually.

Claude Code:

```bash
claude mcp add openrouter --scope user -- uv run --directory /path/to/mcp-openrouter mcp-openrouter
```

Codex:

```bash
codex mcp add openrouter --env OPENROUTER_API_KEY=your-key -- uv run --directory /path/to/mcp-openrouter mcp-openrouter
```

opencode:

```json
{
  "mcp": {
    "openrouter": {
      "type": "local",
      "command": ["uv", "run", "--directory", "/path/to/mcp-openrouter", "mcp-openrouter"],
      "environment": {
        "OPENROUTER_API_KEY": "your-key"
      },
      "enabled": true
    }
  }
}
```

After changing server code, restart the MCP host session so it launches a fresh server process.

## Tech Stack

- [FastMCP](https://gofastmcp.com/) for MCP server and tool registration.
- [OpenRouter](https://openrouter.ai/) for chat, image, embedding, and model catalog APIs.
- [uv](https://docs.astral.sh/uv/) for local dependency management and `uvx` runtime installs.
- [requests](https://requests.readthedocs.io/) for HTTP calls with explicit retry behavior.
- [python-dotenv](https://pypi.org/project/python-dotenv/) for `.env` loading during local development.
- [pytest](https://docs.pytest.org/) and [Ruff](https://docs.astral.sh/ruff/) for test and lint coverage.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENROUTER_API_KEY` is not set | Set it in your shell or `.env`, then restart the MCP host. |
| Installer finds no clients | Make sure `codex`, `claude`, or `opencode` is installed and available on `PATH`. |
| Existing config is skipped | Re-run with `--force` if you want the installer to replace it. |
| Image save fails | `output_path` must be absolute, for example `/Users/you/output.png`. |
| Auth, credit, or rate-limit errors | Check your key and account status at [openrouter.ai/keys](https://openrouter.ai/keys). |
| Local source changes do not appear | Restart the MCP host so the long-lived server process reloads. |

## Publishing Notes

- Publish the Python package to PyPI as `mcp-openrouter`.
- Keep `server.json` in sync with the released package version.
- Preserve the `<!-- mcp-name: io.github.tsilva/mcp-openrouter -->` marker for MCP Registry ownership verification.
- Update `CHANGELOG.md` before release so GitHub release notes stay readable.
- Use the Makefile helper for version bumps:

```bash
make release-1.1.8
```

## Support

Open an issue for bugs, model compatibility problems, or host installation edge cases. Contributions are welcome when they keep the server small, explicit, and easy to verify.

## License

[MIT](LICENSE)
