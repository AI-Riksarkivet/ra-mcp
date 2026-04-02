"""Configuration for SJ railway records search."""

import os


LANCEDB_URI = os.getenv("SJ_LANCEDB_URI", "data/sj")

JUDA_TABLE = "juda"
FIRA_TABLE = "fira"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
