"""Configuration for SBL search."""

import os


LANCEDB_URI = os.getenv("SBL_LANCEDB_URI", "hf://datasets/carpelan/sbl-lance")

SBL_TABLE = "sbl"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
