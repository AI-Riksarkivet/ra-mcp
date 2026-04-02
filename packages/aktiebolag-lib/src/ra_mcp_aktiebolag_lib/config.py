"""Configuration for Aktiebolag records search."""

import os


LANCEDB_URI = os.getenv("AKTIEBOLAG_LANCEDB_URI", "data/aktiebolag")

BOLAG_TABLE = "bolag"
STYRELSE_TABLE = "styrelse"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
