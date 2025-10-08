# Rh  the project
run:
	uv sync
	uv pip install -e .
	uv run fastmcp dev src/oxenstierna/server.py

# Build the project
build:
    uv sync

# Run tests
test: build
    uv run --frozen pytest -xvs tests

# Run ty type checker on all files
typecheck:
    uv run --frozen ty check