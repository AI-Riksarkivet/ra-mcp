"""Configuration for Sjömanshus search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("sjomanshus")

LIGGARE_TABLE = "liggare"
MATRIKEL_TABLE = "matrikel"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
