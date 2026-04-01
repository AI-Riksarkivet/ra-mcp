"""Configuration for Fältjägare search."""

import os


LANCEDB_URI = os.getenv("FALTJAGARE_LANCEDB_URI", "hf://datasets/carpelan/faltjagare-lance")

FALTJAGARE_TABLE = "faltjagare"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
