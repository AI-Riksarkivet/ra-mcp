"""Configuration for diplomatics search."""

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


LANCEDB_URI = os.getenv("DIPLOMATICS_LANCEDB_URI", _resolve_data_path("data/diplomatics"))

SDHK_TABLE = "sdhk"
MPO_TABLE = "mpo"

# IIIF manifest URL templates
SDHK_MANIFEST_TEMPLATE = "https://lbiiif.riksarkivet.se/sdhk!{sdhk_id}/manifest"

# MPO already has iiif_manifest and bildbetrachter columns in the CSV

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
