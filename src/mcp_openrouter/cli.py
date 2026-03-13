"""Command-line interface for mcp-openrouter."""

from __future__ import annotations

import argparse
import sys

from mcp_openrouter.installer import InstallerError, add_install_subparser, run_install
from mcp_openrouter.server import main as serve_main


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="mcp-openrouter")
    subparsers = parser.add_subparsers(dest="command")
    add_install_subparser(subparsers)
    subparsers.add_parser("serve", help="Run the MCP server over stdio")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {None, "serve"}:
        serve_main()
        return 0

    if args.command == "install":
        try:
            return run_install(args)
        except InstallerError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    parser.error(f"Unknown command: {args.command}")
    return 2
