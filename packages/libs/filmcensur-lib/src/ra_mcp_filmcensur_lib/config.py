"""Configuration for filmcensur search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("filmcensur")

FILMREG_TABLE = "filmreg"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
