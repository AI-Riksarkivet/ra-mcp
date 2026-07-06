"""
Configuration constants for search operations.
"""

# Search API URL
SEARCH_API_BASE_URL = "https://data.riksarkivet.se/api/records"

# Request settings
REQUEST_TIMEOUT = 60

# Default values
DEFAULT_LIMIT = 50  # API page size (maps to 'limit' query parameter)
DEFAULT_MAX_DISPLAY = 20

# Upper bound for a single API page (the 'limit' query parameter). The Riksarkivet
# API rejects very large page sizes with an opaque HTTP 400; bounding client-side
# turns that into a clear message. Callers who need more results paginate via offset.
MAX_LIMIT = 1000
