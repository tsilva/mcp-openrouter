#!/bin/bash
set -e

SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_NAME="openrouter"

# Check if settings file exists
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "No Claude settings file found"
    exit 0
fi

# Check if installed (idempotent)
if ! jq -e ".mcpServers.$MCP_NAME" "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo "openrouter MCP not installed"
    exit 0
fi

# Remove MCP server entry
jq 'del(.mcpServers.openrouter)' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"

echo "openrouter MCP uninstalled. Restart Claude Code to apply."
