# ra-mcp-search-cli

CLI command for searching Riksarkivet transcribed documents.

## Usage

```bash
ra search "Stockholm"
ra search "trolldom" --max 50
ra search "(Stockholm AND trolldom)" --max 25
```

## Components

- **app.py**: Typer sub-app registration
- **search_cmd.py**: `ra search` command implementation
- **formatting/**: Rich console output formatting

## Dependencies

- `ra-mcp-search`: Search domain logic
- `typer`: CLI framework
- `rich`: Terminal formatting
