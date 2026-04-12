"""Configuration for DDS church records search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("dds")

FODELSE_TABLE = "fodelse"
DODA_TABLE = "doda"
VIGSEL_TABLE = "vigsel"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
