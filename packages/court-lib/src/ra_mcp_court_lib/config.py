"""Configuration for court records search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("court")

DOMBOKSREGISTER_TABLE = "domboksregister"
MEDELSTAD_TABLE = "medelstad"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
