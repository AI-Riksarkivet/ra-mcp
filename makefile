run:
	uv sync
	uv pip install -e .
	uv run fastmcp dev src/oxenstierna/server.py