"""Configuration for diplomatics search."""

import os


LANCEDB_URI = os.getenv("DIPLOMATICS_LANCEDB_URI", "hf://datasets/carpelan/diplomatics-lance")

SDHK_TABLE = "sdhk"
MPO_TABLE = "mpo"

# IIIF manifest URL templates
SDHK_MANIFEST_TEMPLATE = "https://lbiiif.riksarkivet.se/sdhk!{sdhk_id}/manifest"

# MPO already has iiif_manifest and bildbetrachter columns in the CSV

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
