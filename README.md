<p align="center">
  <img src="https://raw.githubusercontent.com/tsilva/mcp-openrouter/main/logo.png" alt="mcp-openrouter" width="360" />
  <br />
  <!-- repo-tagline:start -->
  <strong>🚀 One MCP server for OpenRouter models 🚀</strong>
  <!-- repo-tagline:end -->
</p>

<!-- mcp-name: io.github.tsilva/mcp-openrouter -->

mcp-openrouter adds OpenRouter chat, images, embeddings, and model discovery
to MCP clients over local stdio.

## Install

Choose the clients to configure:

```bash
uvx mcp-openrouter install --yes --clients codex,claude,opencode
```

The server supports a configured OpenRouter provider through AgentBridge.
See the guide for the gateway environment, tools, and client-specific setup.

[MCP server setup and configuration](https://github.com/tsilva/mcp-openrouter/blob/main/docs/mcp-openrouter-guide.md).

## License

[MIT License](https://github.com/tsilva/mcp-openrouter/blob/main/LICENSE).
