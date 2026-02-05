# ra-mcp-core

Core library for Riksarkivet MCP - provides models, configuration, API clients, formatters, and utilities shared across all ra-mcp packages.

## Installation

```bash
pip install ra-mcp-core
```

## Components

- **config**: API URLs and configuration constants
- **models**: Pydantic data models (SearchHit, SearchResult, BrowseResult, etc.)
- **clients**: API clients for Riksarkivet services (SearchAPI, ALTOClient, OAIPMHClient, IIIFClient)
- **formatters**: Output formatters (PlainTextFormatter, RichConsoleFormatter)
- **utils**: Utility modules (HTTPClient, page_utils, url_generator)

## Usage

```python
from ra_mcp_core import SearchHit, SearchResult
from ra_mcp_core.clients import SearchAPI
from ra_mcp_core.utils.http_client import default_http_client

# Use the search API
search_api = SearchAPI(http_client=default_http_client)
hits, total = search_api.search_transcribed_text("Stockholm", max_results=10)
```
