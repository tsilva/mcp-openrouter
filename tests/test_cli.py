"""Tests for the CLI wrapper."""

from unittest.mock import patch

from mcp_openrouter.cli import main
from mcp_openrouter.installer import InstallerError


class TestCli:
    def test_no_args_runs_server(self):
        with patch("mcp_openrouter.cli.serve_main") as serve_main:
            assert main([]) == 0
        serve_main.assert_called_once_with()

    def test_serve_command_runs_server(self):
        with patch("mcp_openrouter.cli.serve_main") as serve_main:
            assert main(["serve"]) == 0
        serve_main.assert_called_once_with()

    def test_install_command_dispatches_installer(self):
        with patch("mcp_openrouter.cli.run_install", return_value=0) as run_install:
            assert main(["install", "--yes", "--clients", "codex"]) == 0
        run_install.assert_called_once()

    def test_install_errors_return_nonzero(self):
        with patch(
            "mcp_openrouter.cli.run_install",
            side_effect=InstallerError("boom"),
        ):
            assert main(["install", "--yes"]) == 1
