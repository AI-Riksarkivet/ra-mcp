# ra search

Search transcribed historical documents.

```bash
ra search "Stockholm"
ra search "trolldom" --limit 50
ra search "((Stockholm OR Göteborg) AND troll*)"
ra search "Stockholm" --text --include-all-materials
ra search "Stockholm" --max-hits-per-vol 1 --limit 100
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 25 | Maximum records to fetch from API (pagination size) |
| `--max-display` | 10 | Maximum records to display in output |
| `--max-hits-per-vol` | 3 | Limit hits per volume (useful for broad searches) |
| `--transcribed-text` / `--text` | `--transcribed-text` | Search AI-transcribed text (default) or metadata fields |
| `--only-digitised-materials` / `--include-all-materials` | `--only-digitised-materials` | Limit to digitised materials or include all records |
| `--log` | off | Enable API logging to `ra_mcp_api.log` |

`--transcribed-text` requires `--only-digitised-materials`. Using `--include-all-materials` automatically switches to `--text`.

## Search Syntax

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

!!! tip "Use fuzzy search for better results"
    Transcriptions are AI-generated (HTR/OCR) and contain recognition errors. Use fuzzy matching (`~1`) to catch misread characters: `stockholm~1` finds "Stockholm", "Stockholn", "Stookholm", etc.
