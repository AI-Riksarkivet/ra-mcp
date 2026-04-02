"""Configuration for Wincars (Norrland vehicle registration) search."""

import os


LANCEDB_URI = os.getenv("WINCARS_LANCEDB_URI", "data/wincars")

WINCARS_TABLE = "wincars"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
