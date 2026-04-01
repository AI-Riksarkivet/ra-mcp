"""Configuration for Filmcensur search."""

import os


LANCEDB_URI = os.getenv("FILMCENSUR_LANCEDB_URI", "hf://datasets/carpelan/filmcensur-lance")

FILMREG_TABLE = "filmreg"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
