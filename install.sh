#!/bin/bash
set -e

SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_NAME="openrouter"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create settings file if missing
if [ ! -f "$SETTINGS_FILE" ]; then
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo '{}' > "$SETTINGS_FILE"
fi

# Always update to latest MCP structure (handles upgrades)
jq --arg cwd "$REPO_DIR" \
   '.mcpServers.openrouter = {
      "command": "uv",
      "args": ["run", "openrouter-mcp"],
      "cwd": $cwd
    }' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"

# Remind user to create .env if missing
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "Installed openrouter MCP."
    echo ""
    echo "Now create .env file with your API key:"
    echo "  cp $REPO_DIR/.env.example $REPO_DIR/.env"
    echo "  # Edit .env and add your key from https://openrouter.ai/keys"
    echo ""
    echo "Then restart Claude Code."
else
    echo "openrouter MCP installed. Restart Claude Code to apply."
fi
