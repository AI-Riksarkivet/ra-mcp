"""Configuration for SBL search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("sbl")

SBL_TABLE = "sbl"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
