<p align="center">
  <img src="./logo.png" alt="mcp-openrouter" width="360" />
  <br />
  <!-- repo-tagline:start -->
  <strong>🚀 One MCP server for OpenRouter models 🚀</strong>
  <!-- repo-tagline:end -->
</p>

<!-- mcp-name: io.github.tsilva/mcp-openrouter -->

`mcp-openrouter` is a Python MCP server that lets Codex, Claude Code, opencode, and other MCP hosts call OpenRouter models from local stdio tools.

It exposes chat, image generation, embeddings, model listing, and model search through a small FastMCP server with retry handling, host-aware installation, and optional default model environment variables.

## Install

Install the published server into every detected MCP client:

```bash
uvx mcp-openrouter install --yes
```

Install into selected clients:

```bash
uvx mcp-openrouter install --yes --clients codex,claude,opencode
```

Run from a local checkout:

```bash
git clone https://github.com/tsilva/mcp-openrouter.git
cd mcp-openrouter
uv sync --dev
uv run mcp-openrouter
```

`mcp-openrouter` with no arguments starts the stdio server. The explicit command is `uv run mcp-openrouter serve`.

## Commands

```bash
uvx mcp-openrouter install --yes                 # install into detected MCP clients
uvx mcp-openrouter install --yes --force         # replace an existing openrouter config
uvx mcp-openrouter uninstall --yes               # remove from detected MCP clients
uv run mcp-openrouter                            # run the local stdio server
uv run pytest tests/test_cli.py tests/test_client.py tests/test_config.py tests/test_installer.py tests/test_release_metadata.py tests/test_server.py
uv run pytest tests/test_tools.py
uv run ruff check src/
uv run ruff format src/
```

## Tools

| Tool | Purpose |
| --- | --- |
| `chat` | Send a prompt or message list to an OpenRouter chat model. |
| `generate_image` | Generate one image and optionally save it to an absolute local path. |
| `embed` | Generate embeddings for a string or list of strings. |
| `list_models` | List models, optionally filtered by `vision`, `image_gen`, `embedding`, `tools`, or `long_context`. |
| `find_models` | Search model names and slugs, returning up to 20 matches. |

Example MCP prompts:

```text
Use openrouter chat with anthropic/claude-sonnet-4 to summarize this file
Use openrouter generate_image with google/gemini-3-pro-image-preview to create a square app icon
Use openrouter embed with mistralai/mistral-embed-2312 to embed "Hello world"
Use openrouter list_models with capability "image_gen"
Use openrouter find_models to search for "claude"
```

## Configuration

The local gateway needs no application key; upstream credentials stay with
the gateway. The installer rejects
real gateway tokens from `--api-key` or `AGENTBRIDGE_API_KEY` before changing host
configuration; it persists only a non-secret marker. Authenticated remote gateways
need a separately reviewed proxy profile.

Optional defaults make the `model` parameter optional for matching tools:

```bash
DEFAULT_TEXT_MODEL=google/gemini-3-pro-image-preview
DEFAULT_IMAGE_MODEL=google/gemini-3-pro-image-preview
DEFAULT_CODE_MODEL=anthropic/claude-sonnet-4.5
DEFAULT_VISION_MODEL=google/gemini-3-pro-image-preview
DEFAULT_EMBEDDING_MODEL=mistralai/mistral-embed-2312
```

The current tools read `DEFAULT_TEXT_MODEL`, `DEFAULT_IMAGE_MODEL`, and `DEFAULT_EMBEDDING_MODEL`. `DEFAULT_CODE_MODEL` and `DEFAULT_VISION_MODEL` are available for client conventions. Non-secret defaults may remain in `.env`; the API key must not.

## Notes

- Python 3.10+ is required.
- The published runtime command installed into hosts is `uvx mcp-openrouter`.
- Supported installer targets are Codex, Claude Code, and opencode.
- `generate_image.output_path` must be absolute, for example `/Users/you/output.png`.
- Unit tests mock network calls. Live tool tests are opt-in and require a separately authorized proxy session and request content.
- After changing server code, restart the MCP host so it launches a fresh server process.
- Keep `server.json` and the package version in sync before release. Release notes are generated on GitHub. The Makefile release helper is `make release-x.y.z`.

## Local MCP Development

Register a local checkout when you want an MCP host to run your working tree instead of the published PyPI package.

Claude Code:

```bash
claude mcp add openrouter --scope user -- uv run --directory /path/to/mcp-openrouter mcp-openrouter
```

Codex:

```bash
codex mcp add openrouter -- uv run --directory /path/to/mcp-openrouter mcp-openrouter
```

opencode:

```json
{
  "mcp": {
    "openrouter": {
      "type": "local",
      "command": ["uv", "run", "--directory", "/path/to/mcp-openrouter", "mcp-openrouter"],
      "enabled": true
    }
  }
}
```

## Architecture

![mcp-openrouter architecture diagram](./architecture.png)

## AgentBridge routing

All model requests use AgentBridge as their sole endpoint. Set
`AGENTBRIDGE_BASE_URL` to its API root (default
`http://127.0.0.1:8082/api/v1`). `AGENTBRIDGE_API_KEY` is an optional gateway
access token; upstream OpenRouter credentials are managed only by AgentBridge.
Existing model choices are preserved and gain the gateway's `openrouter/`
namespace on requests. Image generation and embeddings require the gateway
application routes; there is no direct-provider fallback.

## License

[MIT](LICENSE)
