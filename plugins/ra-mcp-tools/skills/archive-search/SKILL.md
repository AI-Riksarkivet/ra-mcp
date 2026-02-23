---
name: archive-search
description: >
  Essential pre-search guide — load BEFORE calling search_transcribed or search_metadata.
  Use whenever the user wants to search, find, look up, or discover documents, people,
  places, events, or any information in the Swedish National Archives (Riksarkivet).
  Covers tool selection (search_transcribed vs search_metadata), search strategy,
  Solr query syntax, wildcards, fuzzy matching for OCR/HTR errors, old Swedish
  spelling variants, proximity search, Boolean operators, and pagination workflows.
  Use when: search, find, look up, discover, query, search archives, search documents,
  find person, find place, search records, search court records, search church records,
  search transcriptions, historical research, archival research, Riksarkivet search,
  trolldom, häxprocesser, bouppteckning, dombok, any archive query.
---

# Archive Search Guide

Search strategy, syntax, and best practices for the Riksarkivet search tools
(`search_transcribed` and `search_metadata`).

## Tool Selection

| Research goal | Tool | Key params |
|--------------|------|-----------|
| Find text mentions in court records | search_transcribed | keyword (Solr syntax) |
| Find a person by name | search_metadata | name="Svensson" |
| Find documents from a place | search_metadata | place="Norrköping" |
| Find documents by title/type | search_metadata | keyword="bouppteckning" |
| Church records, estate inventories | search_metadata | keyword + place (not AI-transcribed) |
| Read full page content | browse_document | reference_code, pages |

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
very old/damaged documents. Combine with wildcards for maximum coverage:
`(troll*~1 OR häx*~1)`.

## Search Strategy for Maximum Discovery

1. **Start with transcribed text**: `search_transcribed(keyword, offset=0)` for initial hits
2. **Check metadata too**: `search_metadata` to find documents by title, person, or place
3. **Paginate**: Increase offset by 50 (50, 100, 150...) to discover more matches
4. **Explore related terms**: Search for similar/related words to gather comprehensive context
   - Historical variants and spellings (e.g., "trolldom" + "häxa" + "trollkona")
   - Synonyms and related concepts (e.g., "satan" + "djäfvul" for devil-related terms)
   - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
   - Period-appropriate terminology and archaic spellings
5. **Drill down**: Note reference codes and page numbers from results, then use `browse_document` to examine interesting matches in full

## Critical Search Rules

- **Always group Boolean queries** with parentheses:
  `((skatt* OR guld*) AND (stöld* OR stul*))` — omitting outer parens returns 0 results
- **Use fuzzy search for AI transcription errors**: All text is AI-generated and contains recognition errors.
  `((stöld~2 OR tjufnad~2) AND (silver* OR guld*))` catches misreads and misspellings
- **Account for old Swedish spelling**: Historical documents use archaic forms.
  `(((präst* OR prest*) OR (kyrko* OR kyrck*)) AND ((silver* OR silfv*) OR (guld* OR gull*)))`

## Search Syntax Quick Reference

| Syntax | Example | Meaning |
|--------|---------|---------|
| Exact term | `Stockholm` | Find exact word |
| Wildcard | `Stock*`, `St?ckholm`, `*holm` | Match patterns (* = many chars, ? = one) |
| Fuzzy | `Stockholm~` or `Stockholm~1` | Similar words (edit distance) |
| Proximity | `"Stockholm trolldom"~10` | Two terms within N words |
| Boolean AND | `(Stockholm AND trolldom)` | Both terms required |
| Boolean OR | `(Stockholm OR Göteborg)` | Either term |
| Boolean NOT | `(Stockholm NOT trolldom)` | Exclude term |
| Boosting | `Stockholm^4 trol*` | Increase relevance weight |
| Complex | `((troll* OR häx*) AND (Stockholm OR Göteborg))` | Combine operators |

## Old Swedish Spelling Variants

Common spelling pairs to search for — always try both modern and archaic forms:

| Modern | Archaic / Variant | Context |
|--------|-------------------|---------|
| präst | prest | Priest |
| silver | silfver, silfv | Silver |
| guld | gull | Gold |
| kyrka | kyrcka, kyrck | Church |
| kvinna | qvinna, qwinna | Woman |
| stöld | stöld, tiufnad, tjufnad | Theft |
| häxa | häxa, hexa | Witch |
| trolldom | trolldom, trulldom | Witchcraft |
| djävul | djäfvul, diefvul | Devil |
| ä | æ, e | Vowel variant |
| ö | ø, o | Vowel variant |
| v | f, fv, w | Consonant variant |
| k | ck, c | Consonant variant |

## Proximity Search

Proximity search finds two terms within a specified word distance of each other.

### Rules

- Always wrap both terms in quotes: `"term1 term2"~N` (correct) vs `term1 term2~N` (wrong)
- Only 2 terms work reliably: `"kyrka stöld"~10` (correct) vs `"kyrka silver stöld"~10` (unreliable)
- Distance: `~3` = tight, `~10` = paragraph-level, `~50` = page-level

### Working Examples

**Crime & Punishment:**
```
"tredje stöld"~5           # Third-time theft
"dömd hänga"~10            # Sentenced to hang
"inbrott natt*"~5          # Burglary at night
"kyrka stöld"~10           # Church theft
```

**Values & Items:**
```
"hundra daler"~3           # Hundred dalers
"stor* stöld*"~5           # Major theft
"guld* ring*"~10           # Gold ring
"silver* kalk*"~10         # Silver chalice
```

**Complex Combinations** (Boolean outside quotes):
```
("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*
("inbrott natt*"~5) AND (guld* OR silver*)
("första resan" AND stöld*) OR ("tredje stöld"~5)
```

### Troubleshooting

If proximity search returns no results:
1. **Check your quotes** — must wrap both terms in `"..."`
2. **Reduce to 2 terms** — drop extra words from the phrase
3. **Try exact terms first** — before adding wildcards
4. **Increase distance** — try `~10` instead of `~3`
5. **Simplify wildcards** — use wildcard on one term only

### Reliability by Pattern

| Pattern | Example | Reliability |
|---------|---------|-------------|
| Exact + Exact | `"hundra daler"~3` | Most reliable |
| Exact + Wildcard | `"inbrott natt*"~5` | Reliable |
| Wildcard + Wildcard | `"stor* stöld*"~5` | Sometimes works |

### Layering Strategy

Build from simple to complex, verifying results at each step:
```
Step 1: "kyrka stöld"~10
Step 2: ("kyrka stöld"~10 OR "kyrka tjuv*"~10)
Step 3: (("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*)
Step 4: (("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*) AND (guld* OR silver*)
```

## Best Practices

- **Wildcards for word variations**: `troll*` finds "trolldom", "trolleri", "trollkona"
- **Fuzzy for AI transcription errors**: `Stockholm~1` catches HTR/OCR misreads
- **Year filtering**: Use `year_min`/`year_max` to narrow time periods
- **Sorting**: `sort="timeAsc"` for earliest mentions, `sort="timeDesc"` for most recent
- **Metadata search**: Use dedicated `name` and `place` parameters in `search_metadata`
  for targeted person/place searches instead of putting everything in `keyword`
