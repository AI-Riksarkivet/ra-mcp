"""Configuration for suffrage search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("suffrage")

ROSTRATT_TABLE = "rostratt"
FKPR_TABLE = "fkpr"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
