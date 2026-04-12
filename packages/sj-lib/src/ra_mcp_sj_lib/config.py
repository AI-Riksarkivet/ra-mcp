"""Configuration for SJ railway records search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("sj")

JUDA_TABLE = "juda"
FIRA_TABLE = "fira"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
