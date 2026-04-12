"""Configuration for TORA SPARQL client."""

SPARQL_ENDPOINT = "https://tora.entryscape.net/store/sparql"

# LRU cache size for geocode() — 51K settlements, cache most-queried
GEOCODE_CACHE_SIZE = 4096
