"""Configuration for aktiebolag search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("aktiebolag")

BOLAG_TABLE = "bolag"
STYRELSE_TABLE = "styrelse"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
