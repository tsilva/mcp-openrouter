release-%:
	uv run hatch version $*
	git add pyproject.toml src/mcp_openrouter/__init__.py
	git commit -m "chore: release $$(uv run hatch version)"
	git push
