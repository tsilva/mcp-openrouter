"""Installer for registering mcp-openrouter with supported MCP hosts."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SERVER_NAME = "openrouter"
SUPPORTED_CLIENTS = ("codex", "claude", "opencode")
RUNTIME_COMMAND = ("uvx", "mcp-openrouter")
API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
CLIENT_PROBE_COMMANDS = {
    "codex": ["codex", "mcp", "--help"],
    "claude": ["claude", "mcp", "--help"],
    "opencode": ["opencode", "mcp", "--help"],
}


class InstallerError(RuntimeError):
    """Raised when installation cannot proceed."""


def add_client_selection_arguments(parser: argparse.ArgumentParser, *, action: str) -> None:
    """Add shared client-selection arguments to a subparser."""
    parser.add_argument(
        "--yes",
        action="store_true",
        help=f"{action.capitalize()} all detected clients without selection prompts",
    )
    parser.add_argument(
        "--clients",
        help="Comma-separated list of clients to target: codex,claude,opencode",
    )


def add_install_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add the install subcommand to a parser."""
    parser = subparsers.add_parser(
        "install",
        help="Install mcp-openrouter into supported MCP clients",
    )
    add_client_selection_arguments(parser, action="install into")
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key to persist into installed MCP configs",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing openrouter MCP configs without prompting",
    )


def add_uninstall_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Add the uninstall subcommand to a parser."""
    parser = subparsers.add_parser(
        "uninstall",
        help="Remove mcp-openrouter from supported MCP clients",
    )
    add_client_selection_arguments(parser, action="uninstall from")


def client_supports_mcp(
    client_name: str,
    *,
    runner: Any | None = None,
) -> bool:
    """Return whether the installed client exposes the required MCP commands."""
    command = CLIENT_PROBE_COMMANDS[client_name]
    execute = runner or run_command
    result = execute(command)
    return result.returncode == 0


def detect_clients(
    which: Any = shutil.which,
    *,
    runner: Any | None = None,
) -> dict[str, str]:
    """Return supported clients found on PATH."""
    detected: dict[str, str] = {}
    for name in SUPPORTED_CLIENTS:
        path = which(name)
        if path and client_supports_mcp(name, runner=runner):
            detected[name] = path
    return detected


def ensure_uv_available(which: Any = shutil.which) -> None:
    """Ensure uv is available for running uvx."""
    if which("uv"):
        return
    raise InstallerError(
        "uv is required to install mcp-openrouter. Install it from https://docs.astral.sh/uv/."
    )


def parse_requested_clients(raw_clients: str | None) -> list[str] | None:
    """Parse a comma-separated client list."""
    if raw_clients is None:
        return None

    clients = [item.strip().lower() for item in raw_clients.split(",") if item.strip()]
    if not clients:
        raise InstallerError("No clients were provided to --clients.")

    invalid = sorted(set(clients) - set(SUPPORTED_CLIENTS))
    if invalid:
        allowed = ", ".join(SUPPORTED_CLIENTS)
        raise InstallerError(
            "Unsupported client(s): "
            f"{', '.join(invalid)}. Supported clients: {allowed}."
        )

    deduped: list[str] = []
    for client in clients:
        if client not in deduped:
            deduped.append(client)
    return deduped


def choose_clients(
    detected: dict[str, str],
    requested: list[str] | None,
) -> list[str]:
    """Choose which detected clients are eligible for installation."""
    if requested is not None:
        missing = [client for client in requested if client not in detected]
        if missing:
            raise InstallerError(
                f"Requested client(s) not detected on PATH: {', '.join(missing)}."
            )
        return requested

    return [client for client in SUPPORTED_CLIENTS if client in detected]


def resolve_api_key(explicit_api_key: str | None) -> str:
    """Resolve the OpenRouter API key from args, env, or prompt."""
    for value in (explicit_api_key, os.environ.get(API_KEY_ENV_VAR)):
        if value and value.strip():
            return value.strip()

    if not sys.stdin.isatty():
        raise InstallerError(
            f"{API_KEY_ENV_VAR} is not set. "
            "Pass --api-key or set it in the environment."
        )

    api_key = getpass.getpass("OpenRouter API key: ").strip()
    if not api_key:
        raise InstallerError("OpenRouter API key cannot be empty.")
    return api_key


def prompt_yes_no(prompt: str, *, default: bool = True) -> bool:
    """Prompt the user for a yes/no decision."""
    if not sys.stdin.isatty():
        return default

    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{prompt} {suffix} ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process."""
    return subprocess.run(command, capture_output=True, text=True, check=False)


def format_command(command: list[str]) -> str:
    """Format a command for user-facing output."""
    return " ".join(command)


def read_json_file(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk, returning an empty mapping when missing."""
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise InstallerError(f"Failed to parse JSON at {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise InstallerError(f"Expected a JSON object at {path}.")
    return data


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Atomically write a JSON object to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
        tmp_path = Path(handle.name)
    tmp_path.replace(path)


def normalize_claude_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Claude MCP config for comparison."""
    return {
        "type": config.get("type"),
        "command": config.get("command"),
        "args": list(config.get("args") or []),
        "env": dict(config.get("env") or {}),
    }


def desired_claude_config(api_key: str) -> dict[str, Any]:
    """Return the desired Claude MCP config."""
    return {
        "type": "stdio",
        "command": RUNTIME_COMMAND[0],
        "args": [RUNTIME_COMMAND[1]],
        "env": {API_KEY_ENV_VAR: api_key},
    }


def normalize_opencode_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize an opencode MCP config for comparison."""
    return {
        "type": config.get("type"),
        "command": list(config.get("command") or []),
        "environment": dict(config.get("environment") or {}),
        "enabled": config.get("enabled", True),
    }


def desired_opencode_config(api_key: str) -> dict[str, Any]:
    """Return the desired opencode MCP config."""
    return {
        "type": "local",
        "command": list(RUNTIME_COMMAND),
        "environment": {API_KEY_ENV_VAR: api_key},
        "enabled": True,
    }


def codex_config_matches(config: dict[str, Any]) -> bool:
    """Check whether an existing Codex config matches the desired install."""
    transport = dict(config.get("transport") or {})
    env_names = set(transport.get("env_vars") or [])
    env = transport.get("env")
    if isinstance(env, dict):
        env_names.update(env.keys())

    return (
        transport.get("type") == "stdio"
        and transport.get("command") == RUNTIME_COMMAND[0]
        and list(transport.get("args") or []) == [RUNTIME_COMMAND[1]]
        and API_KEY_ENV_VAR in env_names
    )


def get_existing_codex_server() -> dict[str, Any] | None:
    """Return the current Codex config for openrouter, if any."""
    result = run_command(["codex", "mcp", "list", "--json"])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise InstallerError(f"Failed to inspect Codex MCP servers: {message}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise InstallerError("Failed to parse `codex mcp list --json` output.") from exc

    for item in data:
        if item.get("name") == SERVER_NAME:
            return item
    return None


def get_existing_claude_server(
    config_path: Path | None = None,
) -> dict[str, Any] | None:
    """Return the current Claude config for openrouter, if any."""
    path = config_path or (Path.home() / ".claude.json")
    config = read_json_file(path)
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        return None
    server = servers.get(SERVER_NAME)
    return server if isinstance(server, dict) else None


def get_existing_opencode_server(
    settings_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None, Path]:
    """Return opencode settings, the existing server config, and the settings path."""
    path = settings_path or (Path.home() / ".opencode" / "settings.json")
    settings = read_json_file(path)
    servers = settings.get("mcp")
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        raise InstallerError(f"Expected `mcp` in {path} to be a JSON object.")
    server = servers.get(SERVER_NAME)
    return settings, server if isinstance(server, dict) else None, path


def should_replace(
    client_name: str,
    *,
    force: bool,
    interactive: bool,
) -> bool:
    """Determine whether an existing config should be replaced."""
    if force:
        return True
    if not interactive:
        print(
            f"{client_name}: existing {SERVER_NAME} config differs; "
            "skipping. Use --force to replace."
        )
        return False
    return prompt_yes_no(
        f"{client_name}: replace existing {SERVER_NAME} config?",
        default=False,
    )


def install_codex(api_key: str, *, force: bool, interactive: bool) -> str:
    """Install into Codex via its CLI."""
    existing = get_existing_codex_server()
    if existing and codex_config_matches(existing):
        return "already configured"

    if existing and not should_replace("codex", force=force, interactive=interactive):
        return "skipped"

    if existing:
        remove_result = run_command(["codex", "mcp", "remove", SERVER_NAME])
        if remove_result.returncode != 0:
            message = remove_result.stderr.strip() or remove_result.stdout.strip()
            raise InstallerError(f"Failed to remove existing Codex config: {message}")

    command = [
        "codex",
        "mcp",
        "add",
        SERVER_NAME,
        "--env",
        f"{API_KEY_ENV_VAR}={api_key}",
        "--",
        *RUNTIME_COMMAND,
    ]
    result = run_command(command)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise InstallerError(f"Failed to install into Codex: {message}")
    return "installed"


def install_claude(api_key: str, *, force: bool, interactive: bool) -> str:
    """Install into Claude Code via its CLI."""
    existing = get_existing_claude_server()
    desired = desired_claude_config(api_key)
    if existing and normalize_claude_config(existing) == desired:
        return "already configured"

    if existing and not should_replace("claude", force=force, interactive=interactive):
        return "skipped"

    if existing:
        remove_result = run_command(
            ["claude", "mcp", "remove", "-s", "user", SERVER_NAME]
        )
        if remove_result.returncode != 0:
            message = remove_result.stderr.strip() or remove_result.stdout.strip()
            raise InstallerError(f"Failed to remove existing Claude config: {message}")

    command = [
        "claude",
        "mcp",
        "add",
        "-s",
        "user",
        SERVER_NAME,
        "-e",
        f"{API_KEY_ENV_VAR}={api_key}",
        "--",
        *RUNTIME_COMMAND,
    ]
    result = run_command(command)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise InstallerError(f"Failed to install into Claude Code: {message}")
    return "installed"


def install_opencode(
    api_key: str,
    *,
    force: bool,
    interactive: bool,
    settings_path: Path | None = None,
) -> str:
    """Install into opencode by updating its JSON settings."""
    settings, existing, path = get_existing_opencode_server(settings_path)
    desired = desired_opencode_config(api_key)
    if existing and normalize_opencode_config(existing) == desired:
        return "already configured"

    if existing and not should_replace(
        "opencode",
        force=force,
        interactive=interactive,
    ):
        return "skipped"

    servers = dict(settings.get("mcp") or {})
    servers[SERVER_NAME] = desired
    settings["mcp"] = servers
    write_json_atomic(path, settings)
    return "installed"


def uninstall_codex() -> str:
    """Remove openrouter from Codex."""
    existing = get_existing_codex_server()
    if not existing:
        return "not installed"

    result = run_command(["codex", "mcp", "remove", SERVER_NAME])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise InstallerError(f"Failed to uninstall from Codex: {message}")
    return "uninstalled"


def uninstall_claude() -> str:
    """Remove openrouter from Claude Code."""
    existing = get_existing_claude_server()
    if not existing:
        return "not installed"

    result = run_command(["claude", "mcp", "remove", "-s", "user", SERVER_NAME])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise InstallerError(f"Failed to uninstall from Claude Code: {message}")
    return "uninstalled"


def uninstall_opencode(settings_path: Path | None = None) -> str:
    """Remove openrouter from opencode settings."""
    settings, existing, path = get_existing_opencode_server(settings_path)
    if not existing:
        return "not installed"

    servers = dict(settings.get("mcp") or {})
    servers.pop(SERVER_NAME, None)
    if servers:
        settings["mcp"] = servers
    else:
        settings.pop("mcp", None)
    write_json_atomic(path, settings)
    return "uninstalled"


INSTALLERS = {
    "codex": install_codex,
    "claude": install_claude,
    "opencode": install_opencode,
}

UNINSTALLERS = {
    "codex": uninstall_codex,
    "claude": uninstall_claude,
    "opencode": uninstall_opencode,
}


def resolve_target_clients(args: argparse.Namespace) -> tuple[list[str], list[str], bool]:
    """Resolve detected, eligible, and selected clients for an operation."""
    command_name = getattr(args, "command", "install")
    detected = detect_clients()
    requested = parse_requested_clients(args.clients)
    clients = choose_clients(detected, requested)

    if not clients:
        raise InstallerError(
            "No supported MCP clients detected. "
            "Install Codex, Claude Code, or opencode first."
        )

    interactive = not args.yes and requested is None
    selected: list[str] = []
    if requested is not None or args.yes:
        selected = clients
    else:
        for client in clients:
            if prompt_yes_no(
                f"{command_name.capitalize()} {SERVER_NAME} for {client}?",
                default=True,
            ):
                selected.append(client)

    return clients, selected, interactive


def run_install(args: argparse.Namespace) -> int:
    """Run the installer."""
    ensure_uv_available()
    api_key = resolve_api_key(args.api_key)
    _, selected, interactive = resolve_target_clients(args)

    if not selected:
        print("No clients selected.")
        return 0

    print(f"Using runtime command: {format_command(list(RUNTIME_COMMAND))}")
    for client in selected:
        installer = INSTALLERS[client]
        status = installer(api_key, force=args.force, interactive=interactive)
        print(f"{client}: {status}")

    print("To uninstall later:")
    print(
        "  uvx mcp-openrouter uninstall --yes --clients "
        + ",".join(selected)
    )
    return 0


def run_uninstall(args: argparse.Namespace) -> int:
    """Run the uninstaller."""
    _, selected, _ = resolve_target_clients(args)

    if not selected:
        print("No clients selected.")
        return 0

    for client in selected:
        uninstaller = UNINSTALLERS[client]
        status = uninstaller()
        print(f"{client}: {status}")

    return 0
