release-%:
	uv run hatch version $*
	git add pyproject.toml
	git commit -m "chore: release $$(uv run hatch version)"
	git push
