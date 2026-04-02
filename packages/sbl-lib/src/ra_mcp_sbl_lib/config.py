"""Configuration for SBL search."""

import os


LANCEDB_URI = os.getenv("SBL_LANCEDB_URI", "data/sbl")

SBL_TABLE = "sbl"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
