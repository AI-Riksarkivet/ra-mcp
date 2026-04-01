"""Configuration for Rosenberg geographical lexicon search."""

import os


LANCEDB_URI = os.getenv("ROSENBERG_LANCEDB_URI", "hf://datasets/carpelan/rosenberg-lance")

ROSENBERG_TABLE = "rosenberg"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
