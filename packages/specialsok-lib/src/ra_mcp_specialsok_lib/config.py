"""Configuration for Specialsök datasets search."""

import os


LANCEDB_URI = os.getenv("SPECIALSOK_LANCEDB_URI", "hf://datasets/carpelan/specialsok-lance")

FLYGVAPEN_TABLE = "flygvapenhaverier"
FANGRULLOR_TABLE = "fangrullor"
KURHUSET_TABLE = "kurhuset"
PRESS_TABLE = "presskonferenser"
VIDEO_TABLE = "videobutiker"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
