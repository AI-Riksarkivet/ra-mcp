"""Configuration for DDS church records search."""

import os
from pathlib import Path


def _resolve_data_path(relative: str) -> str:
    """Resolve a data/ path relative to the project root."""
    path = Path(relative)
    if path.is_absolute():
        return relative
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists() and (current / "packages").exists():
            return str(current / relative)
        current = current.parent
    return relative


LANCEDB_URI = os.getenv("DDS_LANCEDB_URI", _resolve_data_path("data/dds"))

FODELSE_TABLE = "fodelse"
DODA_TABLE = "doda"
VIGSEL_TABLE = "vigsel"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
