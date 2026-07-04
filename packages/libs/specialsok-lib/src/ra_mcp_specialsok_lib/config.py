"""Configuration for specialsök search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("specialsok")

FLYGVAPEN_TABLE = "flygvapenhaverier"
FANGRULLOR_TABLE = "fangrullor"
KURHUSET_TABLE = "kurhuset"
PRESS_TABLE = "presskonferenser"
VIDEO_TABLE = "videobutiker"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
