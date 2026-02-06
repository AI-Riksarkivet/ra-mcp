# ra-mcp-browse-cli

CLI command for browsing Riksarkivet document pages.

## Usage

```bash
ra browse "SE/RA/310187/1" --page "7,8,52"
ra browse "SE/RA/420422/01" --pages "1-10"
ra browse "SE/RA/310187/1" --page "7" --search-term "Stockholm"
```

## Components

- **app.py**: Typer sub-app registration
- **browse_cmd.py**: `ra browse` command implementation
- **formatting/**: Rich console output formatting

## Dependencies

- `ra-mcp-browse`: Browse domain logic and API clients
- `typer`: CLI framework
- `rich`: Terminal formatting
