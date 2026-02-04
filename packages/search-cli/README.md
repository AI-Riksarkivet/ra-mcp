# ra-mcp-search-cli

CLI commands for searching and browsing Riksarkivet transcribed documents.

## Features

- **search**: Search for keywords in transcribed materials
- **browse**: Browse specific pages by reference code

## Usage

These commands are integrated into the main `ra` CLI via the server package.

```bash
# Search for documents
ra search "Stockholm"

# Browse specific pages
ra browse "SE/RA/123" --page 5
```

## Dependencies

- `ra-mcp-search`: Core search operations and formatters
- `typer`: CLI framework
- `rich`: Terminal output formatting
