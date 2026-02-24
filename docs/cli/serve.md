# ra serve

Start the MCP server.

```bash
ra serve                              # stdio transport (default)
ra serve --port 7860                  # HTTP transport
ra serve --modules search,browse      # Selective modules
ra serve --list-modules               # Show available modules
ra serve --port 7860 --log            # With API logging
ra serve -v                           # Verbose logging
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | None | Port for HTTP transport (enables HTTP mode when set) |
| `--host` | `localhost` | Host for HTTP transport |
| `--modules` | all defaults | Comma-separated list of modules to enable |
| `--list-modules` | — | List available modules and exit |
| `--log` | off | Enable API logging |
| `-v` / `--verbose` | off | Verbose logging |

---

# ra tui

Interactive terminal browser built with [Textual](https://textual.textualize.io/).

```bash
ra tui                # Launch empty
ra tui "trolldom"     # Launch with pre-filled search
```

## Keybindings

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
