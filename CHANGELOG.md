# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and versions are tracked from the published package version.

## [Unreleased]

- No unreleased changes yet.

## [1.1.8] - 2026-04-28

### Changed

- Excluded the unused generated sample image from source distributions to keep release artifacts small.

## [1.1.7] - 2026-03-17

### Added

- Guided install and uninstall commands for Codex, Claude Code, and opencode.
- MCP Registry metadata in `server.json` for the public registry entry.
- Configurable default models for text, image, code, vision, and embedding use cases.
- Curated release notes generation from this changelog during GitHub releases.
- Release metadata checks and built-artifact smoke tests in CI.

### Changed

- Expanded model discovery so image and embedding capabilities are merged from the public models API.
- Improved README coverage for production installation, configuration, troubleshooting, and publishing.
- Switched OpenRouter attribution headers to neutral `mcp-openrouter` branding.

### Fixed

- Corrected API documentation so `generate_image.output_path` is documented as optional.
- Added coverage to keep package metadata and `server.json` versions in sync.
