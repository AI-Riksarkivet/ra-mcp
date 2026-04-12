"""Configuration for fältjägare search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("faltjagare")

FALTJAGARE_TABLE = "faltjagare"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
