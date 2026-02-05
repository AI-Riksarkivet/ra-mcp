# ra-mcp-browse-cli

CLI command for browsing Riksarkivet document pages.

## Features

- **browse**: Browse specific pages by reference code with rich console output
- Retrieves full transcribed text, ALTO XML, and document metadata
- Highlights search terms
- Links to IIIF images and bildvisning viewer

## Usage

```bash
# Browse specific pages
ra browse "SE/RA/310187/1" --page "7,8,52"

# Browse page range
ra browse "SE/RA/420422/01" --pages "1-10"

# Browse with search term highlighting
ra browse "SE/RA/310187/1" --page "7,8" --search-term "Stockholm"
```

## Dependencies

- `ra-mcp-browse`: Core browse operations and clients
- `typer`: CLI framework
- `rich`: Terminal formatting
