"""Configuration for Rosenberg search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("rosenberg")

ROSENBERG_TABLE = "rosenberg"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
