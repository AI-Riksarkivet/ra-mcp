"""
Configuration constants for Riksarkivet MCP server.
"""

# API Base URLs
SEARCH_API_BASE_URL = "https://data.riksarkivet.se/api/records"
COLLECTION_API_BASE_URL = "https://lbiiif.riksarkivet.se/collection/arkiv"
IIIF_BASE_URL = "https://lbiiif.riksarkivet.se"
OAI_BASE_URL = "https://oai-pmh.riksarkivet.se/OAI"

# Request settings
REQUEST_TIMEOUT = 60

# Default values
DEFAULT_MAX_RESULTS = 50
DEFAULT_MAX_DISPLAY = 20
DEFAULT_MAX_PAGES = 10

# XML Namespaces
NAMESPACES = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ead': 'urn:isbn:1-931666-22-9',
    'xlink': 'http://www.w3.org/1999/xlink'
}

# ALTO XML Namespaces
ALTO_NAMESPACES = [
    {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'},
    {'alto': 'http://www.loc.gov/standards/alto/ns-v2#'},
    {'alto': 'http://www.loc.gov/standards/alto/ns-v3#'},
]