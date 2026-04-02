"""Configuration for Suffrage search."""

import os


LANCEDB_URI = os.getenv("SUFFRAGE_LANCEDB_URI", "data/suffrage")

ROSTRATT_TABLE = "rostratt"
FKPR_TABLE = "fkpr"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
