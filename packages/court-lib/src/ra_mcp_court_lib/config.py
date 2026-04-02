"""Configuration for court records search."""

import os


LANCEDB_URI = os.getenv("COURT_LANCEDB_URI", "data/court")

DOMBOKSREGISTER_TABLE = "domboksregister"
MEDELSTAD_TABLE = "medelstad"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
