# ra search

Search transcribed historical documents.

```bash
ra search "Stockholm"
ra search "trolldom" --limit 50
ra search "Stockholm troll*"
ra search "Stockholm" --text --include-all-materials
ra search "Stockholm" --max-hits-per-vol 1 --limit 100
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 50 | Records to fetch from API per request (pagination size), 1–1000; paginate for more |
| `--max-display` | 20 | Maximum records to display in output |
| `--max-hits-per-vol` | 3 | Limit hits per volume (useful for broad searches) |
| `--transcribed-text` / `--text` | `--transcribed-text` | Search AI-transcribed text (default) or metadata fields |
| `--only-digitised-materials` / `--include-all-materials` | `--only-digitised-materials` | Limit to digitised materials or include all records |
| `--log` | off | Enable API logging to `ra_mcp_api.log` |

`--transcribed-text` requires `--only-digitised-materials`. Using `--include-all-materials` automatically switches to `--text`.

## Search Syntax

The search API is a plain free-text engine (verified against the live API — it
is not a full Solr/Lucene endpoint):

| Syntax | Example | Meaning |
|--------|---------|---------|
| Exact term | `Stockholm` | Find exact word |
| Several terms | `pest smitta` | All terms required in the same document (implicit AND) |
| Wildcard | `troll*`, `St?ckholm` | Pattern matching (`*` = many chars, `?` = one) |
| Fuzzy | `Stockholm~1` | Similar words (edit distance) |

Boolean operators (`AND`/`OR`/`NOT`) are **not supported** — the API matches
them as literal words (`and` alone matches 1.6M volumes), so such queries are
rejected with a corrective message. There is no OR syntax: run one search per
alternative term instead. Quoted phrases and proximity (`"a b"~10`) always
return 0 on transcribed text — even for a phrase that occurs verbatim on a
page — so quoted queries are rejected too.

!!! tip "Use fuzzy search for better results"
    Transcriptions are AI-generated (HTR/OCR) and contain recognition errors. Use fuzzy matching (`~1`) to catch misread characters: `stockholm~1` finds "Stockholm", "Stockholn", "Stookholm", etc.

Malformed queries (unbalanced parentheses or quotes, e.g. `(((`) and boolean-operator queries are rejected with a clear message rather than silently returning unintended results.

For historical place names and why fuzzy search matters so much on HTR text, see [Search Tips](../how-it-works/search-tips.md).
