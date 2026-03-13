"""Unit tests for the installer."""

import argparse
import json
from unittest.mock import patch

import pytest

from mcp_openrouter import installer as installer_module
from mcp_openrouter.installer import (
    API_KEY_ENV_VAR,
    SERVER_NAME,
    InstallerError,
    choose_clients,
    client_supports_mcp,
    codex_config_matches,
    desired_claude_config,
    desired_opencode_config,
    detect_clients,
    install_claude,
    install_codex,
    install_opencode,
    parse_requested_clients,
    resolve_api_key,
    run_install,
)


class TestDetectClients:
    def test_detects_supported_clients(self):
        detected = detect_clients(
            which=lambda name: {
                "codex": "/usr/bin/codex",
                "claude": None,
                "opencode": "/usr/bin/opencode",
            }.get(name),
            runner=lambda command: argparse.Namespace(returncode=0),
        )

        assert detected == {
            "codex": "/usr/bin/codex",
            "opencode": "/usr/bin/opencode",
        }

    def test_skips_clients_without_mcp_support(self):
        detected = detect_clients(
            which=lambda name: {
                "codex": "/usr/bin/codex",
                "claude": "/usr/bin/claude",
            }.get(name),
            runner=lambda command: argparse.Namespace(
                returncode=0 if command[0] == "codex" else 1
            ),
        )

        assert detected == {"codex": "/usr/bin/codex"}


class TestClientSupportProbe:
    def test_reports_supported_client(self):
        assert (
            client_supports_mcp(
                "claude",
                runner=lambda command: argparse.Namespace(returncode=0),
            )
            is True
        )

    def test_reports_unsupported_client(self):
        assert (
            client_supports_mcp(
                "claude",
                runner=lambda command: argparse.Namespace(returncode=1),
            )
            is False
        )


class TestRequestedClients:
    def test_parses_and_deduplicates(self):
        assert parse_requested_clients("codex, claude,codex") == ["codex", "claude"]

    def test_rejects_invalid_clients(self):
        with pytest.raises(InstallerError, match="Unsupported client"):
            parse_requested_clients("codex,bad-client")

    def test_choose_clients_rejects_missing_detection(self):
        with pytest.raises(InstallerError, match="not detected"):
            choose_clients({"codex": "/usr/bin/codex"}, ["codex", "claude"])


class TestResolveApiKey:
    def test_prefers_explicit_api_key(self):
        assert resolve_api_key("sk-test") == "sk-test"

    def test_uses_environment(self, monkeypatch):
        monkeypatch.setenv(API_KEY_ENV_VAR, "sk-env")
        assert resolve_api_key(None) == "sk-env"

    def test_prompts_when_missing(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        with patch("getpass.getpass", return_value="sk-prompt"):
            assert resolve_api_key(None) == "sk-prompt"

    def test_errors_without_tty(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        with pytest.raises(InstallerError, match=API_KEY_ENV_VAR):
            resolve_api_key(None)


class TestCodexInstaller:
    def test_codex_match_accepts_uvx_runtime(self):
        config = {
            "transport": {
                "type": "stdio",
                "command": "uvx",
                "args": ["mcp-openrouter"],
                "env_vars": [API_KEY_ENV_VAR],
            }
        }
        assert codex_config_matches(config) is True

    def test_skips_replace_without_force_in_noninteractive_mode(self):
        existing = {
            "transport": {
                "type": "stdio",
                "command": "uv",
                "args": ["run", "mcp-openrouter"],
                "env_vars": [],
            }
        }
        with patch(
            "mcp_openrouter.installer.get_existing_codex_server",
            return_value=existing,
        ), patch("mcp_openrouter.installer.run_command") as run_command:
            status = install_codex("sk-key", force=False, interactive=False)

        assert status == "skipped"
        run_command.assert_not_called()

    def test_replaces_existing_config_when_forced(self):
        existing = {
            "transport": {
                "type": "stdio",
                "command": "uv",
                "args": ["run", "mcp-openrouter"],
                "env_vars": [],
            }
        }
        with patch(
            "mcp_openrouter.installer.get_existing_codex_server",
            return_value=existing,
        ), patch(
            "mcp_openrouter.installer.run_command",
            side_effect=[
                argparse.Namespace(returncode=0, stderr="", stdout=""),
                argparse.Namespace(returncode=0, stderr="", stdout=""),
            ],
        ) as run_command:
            status = install_codex("sk-key", force=True, interactive=False)

        assert status == "installed"
        assert run_command.call_args_list[0].args[0] == [
            "codex",
            "mcp",
            "remove",
            SERVER_NAME,
        ]
        assert run_command.call_args_list[1].args[0] == [
            "codex",
            "mcp",
            "add",
            SERVER_NAME,
            "--env",
            f"{API_KEY_ENV_VAR}=sk-key",
            "--",
            "uvx",
            "mcp-openrouter",
        ]


class TestClaudeInstaller:
    def test_skips_when_already_configured(self):
        existing = desired_claude_config("sk-key")
        with patch(
            "mcp_openrouter.installer.get_existing_claude_server",
            return_value=existing,
        ), patch("mcp_openrouter.installer.run_command") as run_command:
            status = install_claude("sk-key", force=False, interactive=False)

        assert status == "already configured"
        run_command.assert_not_called()

    def test_replaces_existing_config_when_forced(self):
        existing = {
            "type": "stdio",
            "command": "uv",
            "args": ["run", "mcp-openrouter"],
            "env": {},
        }
        with patch(
            "mcp_openrouter.installer.get_existing_claude_server",
            return_value=existing,
        ), patch(
            "mcp_openrouter.installer.run_command",
            side_effect=[
                argparse.Namespace(returncode=0, stderr="", stdout=""),
                argparse.Namespace(returncode=0, stderr="", stdout=""),
            ],
        ) as run_command:
            status = install_claude("sk-key", force=True, interactive=False)

        assert status == "installed"
        assert run_command.call_args_list[0].args[0] == [
            "claude",
            "mcp",
            "remove",
            "-s",
            "user",
            SERVER_NAME,
        ]
        assert run_command.call_args_list[1].args[0] == [
            "claude",
            "mcp",
            "add",
            "-s",
            "user",
            "-e",
            f"{API_KEY_ENV_VAR}=sk-key",
            SERVER_NAME,
            "--",
            "uvx",
            "mcp-openrouter",
        ]


class TestOpencodeInstaller:
    def test_merges_into_empty_settings(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{}\n")

        status = install_opencode(
            "sk-key",
            force=False,
            interactive=False,
            settings_path=settings_path,
        )

        assert status == "installed"
        data = json.loads(settings_path.read_text())
        assert data["mcp"][SERVER_NAME] == desired_opencode_config("sk-key")

    def test_preserves_unrelated_settings(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "theme": "dark",
                    "mcp": {
                        "other": {"type": "local", "command": ["echo", "ok"]},
                    },
                }
            )
        )

        status = install_opencode(
            "sk-key",
            force=False,
            interactive=False,
            settings_path=settings_path,
        )

        assert status == "installed"
        data = json.loads(settings_path.read_text())
        assert data["theme"] == "dark"
        assert data["mcp"]["other"] == {"type": "local", "command": ["echo", "ok"]}
        assert data["mcp"][SERVER_NAME] == desired_opencode_config("sk-key")

    def test_skips_replace_without_force(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps(
                {
                    "mcp": {
                        SERVER_NAME: {
                            "type": "local",
                            "command": ["python", "-m", "x"],
                        },
                    }
                }
            )
        )

        status = install_opencode(
            "sk-key",
            force=False,
            interactive=False,
            settings_path=settings_path,
        )

        assert status == "skipped"


class TestRunInstall:
    def test_missing_uv_raises(self):
        args = argparse.Namespace(yes=False, clients=None, api_key=None, force=False)
        with patch(
            "mcp_openrouter.installer.ensure_uv_available",
            side_effect=InstallerError("uv missing"),
        ):
            with pytest.raises(InstallerError, match="uv missing"):
                run_install(args)

    def test_yes_installs_all_selected_clients(self, monkeypatch):
        args = argparse.Namespace(
            yes=True,
            clients="codex,claude",
            api_key="sk-key",
            force=False,
        )
        monkeypatch.setattr(
            "mcp_openrouter.installer.ensure_uv_available",
            lambda: None,
        )
        monkeypatch.setattr(
            "mcp_openrouter.installer.detect_clients",
            lambda: {"codex": "/usr/bin/codex", "claude": "/usr/bin/claude"},
        )
        monkeypatch.setitem(
            installer_module.INSTALLERS,
            "codex",
            lambda api_key, force, interactive: "installed",
        )
        monkeypatch.setitem(
            installer_module.INSTALLERS,
            "claude",
            lambda api_key, force, interactive: "already configured",
        )

        assert run_install(args) == 0
