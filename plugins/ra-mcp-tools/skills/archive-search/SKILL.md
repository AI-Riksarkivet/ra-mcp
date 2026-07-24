---
name: archive-search
description: >
  How to query the Riksarkivet search tools — load BEFORE calling
  search_transcribed or search_metadata. Picks the right tool and builds
  queries with the fuzzy, wildcard, and old-Swedish-spelling tactics that AI
  transcription errors demand.
  Use when the user wants to search, find, or look up documents, people, places,
  or events in the Swedish National Archives (Riksarkivet) — including terms like
  trolldom, häxprocess, bouppteckning, or dombok.
---

# Archive Search Guide

Search strategy, syntax, and best practices for the Riksarkivet search tools
(`search_transcribed` and `search_metadata`).

## Tool Selection

| Research goal | Tool | Key params |
|--------------|------|-----------|
| Find text mentions in court records | search_transcribed | keyword |
| Find a person by name | search_metadata | name="Svensson" |
| Find documents from a place | search_metadata | place="Norrköping" |
| Find documents by title/type | search_metadata | keyword="bouppteckning" |
| Church records, estate inventories | search_metadata | keyword + place (not AI-transcribed) |
| Read full page content | browse_document | reference_code, pages |

## Query Syntax — What Actually Works

The search API is a plain free-text engine, NOT a full Solr/Lucene endpoint.
Every syntax claim below is verified against the live API.

| Syntax | Example | Meaning |
|--------|---------|---------|
| Single term | `Stockholm` | Find the word |
| Several terms | `pest smitta` | ALL terms required in the same document (implicit AND) |
| Exact phrase | `"Ostindiska kompaniet"` | Words adjacent, in this order |
| Wildcard | `troll*`, `st?ckholm`, `*holm` | `*` = many chars, `?` = one char |
| Fuzzy | `Stockholm~1` | Similar words (edit distance) |

**NOT supported — never use:**

- **`AND` / `OR` / `NOT` / `|` / parentheses.** There is no boolean parser. The
  words AND/OR/NOT are searched as literal text: `and` alone matches 1.6M
  volumes, so `pest AND smitta` returns ~1.64M junk hits instead of the
  33-document conjunction `pest smitta`. The server rejects such queries.
- **OR-logic has no syntax at all.** Run one search per alternative term
  instead: search `troll*`, then `häx*`, and merge what you learn.
- **Proximity `"a b"~10`.** The slop is not honored — the query behaves as the
  exact phrase. Use plain multi-term search (`kyrka stöld` = both words
  anywhere in the volume) or an exact phrase instead.
- **Boosting (`term^4`).** Unverified; adds nothing. Leave it out.

## Transcription Quality — Why Fuzzy Search Matters

All searchable text is **AI-generated** using HTR (Handwritten Text Recognition) and OCR models.
These transcriptions contain recognition errors: misread characters, merged or split words, and
garbled passages — especially in older, damaged, or poorly legible documents.

**Always use fuzzy search (~) by default** to compensate for transcription errors:

- `stockholm~1` finds "Stockholm", "Stockholn", "Stookholm" (common HTR misreads)
- `trolldom~1` finds "trolldom", "trolldoin", "trolldorn"
- `präst~1` finds "präst", "prast", "prest"

Without fuzzy search, you will **miss many relevant results** because the transcription
of the exact word you're looking for may contain errors.

**Rule of thumb**: Use `~1` (edit distance 1) for short words, `~2` for longer words or
very old/damaged documents. For stem variants use a wildcard instead: `troll*`.

## Search Strategy for Maximum Discovery

1. **Start with transcribed text**: `search_transcribed(keyword, offset=0)` for initial hits
2. **Check metadata too**: `search_metadata` to find documents by title, person, or place
3. **Paginate**: Increase offset by 50 (50, 100, 150...) to discover more matches
4. **Explore related terms — one search each** (this replaces OR):
   - Historical variants and spellings (e.g., "trolldom", then "häxa", then "trollkona")
   - Synonyms and related concepts (e.g., "satan", then "djäfvul" for devil-related terms)
   - Different word forms (e.g., "trolleri", then "trollkonst")
   - Period-appropriate terminology and archaic spellings
5. **Narrow with more terms**: adding a word tightens the search — `pest smitta`
   returns only documents containing both
6. **Drill down**: Note reference codes and page numbers from results, then use
   `browse_document` to examine interesting matches in full

## Old Swedish Spelling Variants

Common spelling pairs to search for — always try both modern and archaic forms
(as separate searches, or covered by one wildcard/fuzzy term):

| Modern | Archaic / Variant | Covered by |
|--------|-------------------|-----------|
| präst | prest | `pr?st` or `präst~1` |
| silver | silfver, silfv | `sil*er` or `silf*` |
| guld | gull | `gul*` |
| kyrka | kyrcka, kyrck | `kyrk*` or `kyrck*` |
| kvinna | qvinna, qwinna | `q*inna` or `kvinna~1` |
| stöld | tiufnad, tjufnad | separate searches |
| häxa | hexa | `h?xa` |
| trolldom | trulldom | `tr?lldom` |
| djävul | djäfvul, diefvul | `dj?f*` + separate searches |

General letter drift: ä↔æ/e, ö↔ø/o, v↔f/fv/w, k↔ck/c — `?` and `~1` absorb most of it.

## Best Practices

- **Wildcards for word variations**: `troll*` finds "trolldom", "trolleri", "trollkona"
- **Fuzzy for AI transcription errors**: `Stockholm~1` catches HTR/OCR misreads
- **Multi-term to require co-occurrence**: `kyrka stöld silver` = volumes containing all three
- **Year filtering**: Use `year_min`/`year_max` to narrow time periods
- **Sorting**: `sort="timeAsc"` for earliest mentions, `sort="timeDesc"` for most recent
- **Metadata search**: Use dedicated `name` and `place` parameters in `search_metadata`
  for targeted person/place searches instead of putting everything in `keyword`
