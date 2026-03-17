"""Release metadata consistency checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = (ROOT / "pyproject.toml").read_text()


def _pyproject_value(section: str, key: str) -> str:
    pattern = rf"(?ms)^\[{re.escape(section)}\]\n.*?^{re.escape(key)} = \"([^\"]+)\""
    match = re.search(pattern, PYPROJECT)
    if not match:
        raise AssertionError(f"Could not find {key} in [{section}]")
    return match.group(1)


def _project_version() -> str:
    version_path = _pyproject_value("tool.hatch.version", "path")
    content = (ROOT / version_path).read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise AssertionError(f"Could not find __version__ in {version_path}")
    return match.group(1)


def test_server_json_matches_package_version():
    version = _project_version()
    server_metadata = json.loads((ROOT / "server.json").read_text())

    assert server_metadata["version"] == version
    assert server_metadata["packages"][0]["version"] == version


def test_server_json_matches_package_name():
    project_name = _pyproject_value("project", "name")
    server_metadata = json.loads((ROOT / "server.json").read_text())

    assert server_metadata["packages"][0]["identifier"] == project_name
