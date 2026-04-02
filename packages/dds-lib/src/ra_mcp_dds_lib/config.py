"""Configuration for DDS (church records) search."""

import os


LANCEDB_URI = os.getenv("DDS_LANCEDB_URI", "data/dds")

FODELSE_TABLE = "fodelse"
DODA_TABLE = "doda"
VIGSEL_TABLE = "vigsel"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
