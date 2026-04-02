"""Configuration for Filmcensur search."""

import os


LANCEDB_URI = os.getenv("FILMCENSUR_LANCEDB_URI", "data/filmcensur")

FILMREG_TABLE = "filmreg"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
