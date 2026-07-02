"""Configuration for diplomatics search."""

from ra_mcp_common.datasets import resolve_dataset_path


LANCEDB_URI = resolve_dataset_path("diplomatics")

SDHK_TABLE = "sdhk"
MPO_TABLE = "mpo"

# IIIF manifest URL templates
SDHK_MANIFEST_TEMPLATE = "https://lbiiif.riksarkivet.se/sdhk!{sdhk_id}/manifest"

# MPO already has iiif_manifest and bildbetrachter columns in the CSV

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
