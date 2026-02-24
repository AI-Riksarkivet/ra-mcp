# ra browse

Browse pages by reference code.

```bash
ra browse "SE/RA/310187/1" --page "7,8,52"
ra browse "SE/RA/420422/01" --pages "1-10"
ra browse "SE/RA/310187/1" --page "7" --search-term "Stockholm"
ra browse "SE/RA/420422/01" --pages "1-5" --show-links
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--pages` / `--page` | `1-20` | Page specification (see below) |
| `--search-term` | None | Highlight keyword in transcribed text |
| `--max-display` | 20 | Maximum pages to display |
| `--show-links` | off | Show ALTO XML, IIIF image, and Bildvisaren URLs |
| `--log` | off | Enable API logging to `ra_mcp_api.log` |

## Page Specification

| Format | Example | Description |
|--------|---------|-------------|
| Single | `"5"` | One page |
| Range | `"1-10"` | Pages 1 through 10 |
| List | `"5,7,9"` | Specific pages |

`--page` and `--pages` are interchangeable aliases.
