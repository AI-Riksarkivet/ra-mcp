"""Configuration for diplomatics search."""

import os
from pathlib import Path


LANCEDB_PATH = Path(os.getenv("DIPLOMATICS_LANCEDB_PATH", "data/diplomatics"))

SDHK_TABLE = "sdhk"
MPO_TABLE = "mpo"

# IIIF manifest URL templates
SDHK_MANIFEST_TEMPLATE = "https://lbiiif.riksarkivet.se/sdhk!{sdhk_id}/manifest"

# MPO already has iiif_manifest and bildbetrachter columns in the CSV

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
