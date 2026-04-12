"""Configuration for Wincars vehicle register search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("wincars")

WINCARS_TABLE = "wincars"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
