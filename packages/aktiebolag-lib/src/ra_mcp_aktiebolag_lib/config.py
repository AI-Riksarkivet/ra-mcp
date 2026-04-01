"""Configuration for Aktiebolag records search."""

import os


LANCEDB_URI = os.getenv("AKTIEBOLAG_LANCEDB_URI", "hf://datasets/carpelan/aktiebolag-lance")

BOLAG_TABLE = "bolag"
STYRELSE_TABLE = "styrelse"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
