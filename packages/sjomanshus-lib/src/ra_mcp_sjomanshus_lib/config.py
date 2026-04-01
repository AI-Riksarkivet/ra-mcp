"""Configuration for Sjömanshus search."""

import os


LANCEDB_URI = os.getenv("SJOMANSHUS_LANCEDB_URI", "hf://datasets/carpelan/sjomanshus-lance")

LIGGARE_TABLE = "liggare"
MATRIKEL_TABLE = "matrikel"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
