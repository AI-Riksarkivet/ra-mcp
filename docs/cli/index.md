---
icon: lucide/terminal
---

# CLI Reference

The ra-mcp CLI provides terminal access to the same operations available through MCP tools.

```bash
uv pip install ra-mcp           # Server + MCP tools
uv pip install ra-mcp[cli]      # Add CLI commands (ra search, ra browse)
uv pip install ra-mcp[tui]      # Add interactive TUI (ra tui)
```

---

## ra search

Search transcribed historical documents.

```bash
ra search "Stockholm"
ra search "trolldom" --limit 50
ra search "((Stockholm OR Göteborg) AND troll*)"
ra search "Stockholm" --text --include-all-materials
ra search "Stockholm" --max-hits-per-vol 1 --limit 100
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 25 | Maximum records to fetch from API (pagination size) |
| `--max-display` | 10 | Maximum records to display in output |
| `--max-hits-per-vol` | 3 | Limit hits per volume (useful for broad searches) |
| `--transcribed-text` / `--text` | `--transcribed-text` | Search AI-transcribed text (default) or metadata fields |
| `--only-digitised-materials` / `--include-all-materials` | `--only-digitised-materials` | Limit to digitised materials or include all records |
| `--log` | off | Enable API logging to `ra_mcp_api.log` |

`--transcribed-text` requires `--only-digitised-materials`. Using `--include-all-materials` automatically switches to `--text`.

### Search Syntax

The search supports full Solr query syntax:

| Syntax | Example | Meaning |
|--------|---------|---------|
| Exact term | `Stockholm` | Find exact word |
| Wildcard | `troll*`, `St?ckholm` | Pattern matching |
| Fuzzy | `Stockholm~1` | Similar words (edit distance) |
| Proximity | `"Stockholm trolldom"~10` | Two terms within N words |
| Boolean AND | `(Stockholm AND trolldom)` | Both terms required |
| Boolean OR | `(Stockholm OR Göteborg)` | Either term |
| Boolean NOT | `(Stockholm NOT trolldom)` | Exclude term |

Always wrap Boolean queries in parentheses: `((A OR B) AND C*)`.

---

## ra browse

Browse pages by reference code.

```bash
ra browse "SE/RA/310187/1" --page "7,8,52"
ra browse "SE/RA/420422/01" --pages "1-10"
ra browse "SE/RA/310187/1" --page "7" --search-term "Stockholm"
ra browse "SE/RA/420422/01" --pages "1-5" --show-links
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--pages` / `--page` | `1-20` | Page specification (see below) |
| `--search-term` | None | Highlight keyword in transcribed text |
| `--max-display` | 20 | Maximum pages to display |
| `--show-links` | off | Show ALTO XML, IIIF image, and Bildvisaren URLs |
| `--log` | off | Enable API logging to `ra_mcp_api.log` |

### Page Specification

| Format | Example | Description |
|--------|---------|-------------|
| Single | `"5"` | One page |
| Range | `"1-10"` | Pages 1 through 10 |
| List | `"5,7,9"` | Specific pages |

`--page` and `--pages` are interchangeable aliases.

---

## ra tui

Interactive terminal browser built with [Textual](https://textual.textualize.io/).

```bash
ra tui                # Launch empty
ra tui "trolldom"     # Launch with pre-filled search
```

### Keybindings

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `Enter` | Submit search / Open selected item |
| `Escape` | Go back / Clear search |
| `m` | Toggle search mode (Transcribed / Metadata) |
| `n` / `p` | Next / Previous page of results |
| `o` | Open in browser |
| `y` | Copy reference code to clipboard |
| `c` | Copy page text to clipboard (page viewer) |
| `a` | Copy ALTO XML URL to clipboard (page viewer) |
| `?` | Show keybindings help |
| `q` | Quit |

---

## ra serve

Start the MCP server.

```bash
ra serve                              # stdio transport (default)
ra serve --port 7860                  # HTTP transport
ra serve --modules search,browse      # Selective modules
ra serve --list-modules               # Show available modules
ra serve --port 7860 --log            # With API logging
ra serve -v                           # Verbose logging
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | None | Port for HTTP transport (enables HTTP mode when set) |
| `--host` | `localhost` | Host for HTTP transport |
| `--modules` | all defaults | Comma-separated list of modules to enable |
| `--list-modules` | — | List available modules and exit |
| `--log` | off | Enable API logging |
| `-v` / `--verbose` | off | Verbose logging |
