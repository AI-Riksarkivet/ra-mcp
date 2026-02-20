---
name: archive-search
description: >
  Guide for searching historical documents in the Swedish National Archives.
  Covers Solr query syntax, search strategy, OCR/HTR fuzzy matching, old Swedish
  spelling variants, proximity search, Boolean operators, and pagination workflows.
  Use when: search archives, query syntax, wildcards, fuzzy search, proximity search,
  Boolean operators, OCR errors, old Swedish spelling, search strategy,
  Solr syntax, find historical documents, search transcriptions.
---

# Archive Search Guide

Search strategy, syntax, and best practices for the Riksarkivet search tools
(`search_transcribed` and `search_metadata`).

## Search Strategy for Maximum Discovery

1. **Start with transcribed text**: `search_transcribed(keyword, offset=0)` for initial hits
2. **Check metadata too**: `search_metadata` to find documents by title, person, or place
3. **Paginate**: Increase offset by 50 (50, 100, 150...) to discover more matches
4. **Explore related terms**: Search for similar/related words to gather comprehensive context
   - Historical variants and spellings (e.g., "trolldom" + "haxa" + "trollkona")
   - Synonyms and related concepts (e.g., "satan" + "djafvul" for devil-related terms)
   - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
   - Period-appropriate terminology and archaic spellings
5. **Drill down**: Note reference codes and page numbers from results, then use `browse_document` to examine interesting matches in full

## Critical Search Rules

- **Always group Boolean queries** with parentheses:
  `((skatt* OR guld*) AND (stold* OR stul*))` — omitting outer parens returns 0 results
- **Use fuzzy search for OCR/HTR errors**: Many transcriptions have AI recognition errors.
  `((stold~2 OR tjufnad~2) AND (silver* OR guld*))` catches misspellings
- **Account for old Swedish spelling**: Historical documents use archaic forms.
  `(((prast* OR prest*) OR (kyrko* OR kyrck*)) AND ((silver* OR silfv*) OR (guld* OR gull*)))`

## Search Syntax Quick Reference

| Syntax | Example | Meaning |
|--------|---------|---------|
| Exact term | `Stockholm` | Find exact word |
| Wildcard | `Stock*`, `St?ckholm`, `*holm` | Match patterns (* = many chars, ? = one) |
| Fuzzy | `Stockholm~` or `Stockholm~1` | Similar words (edit distance) |
| Proximity | `"Stockholm trolldom"~10` | Two terms within N words |
| Boolean AND | `(Stockholm AND trolldom)` | Both terms required |
| Boolean OR | `(Stockholm OR Goteborg)` | Either term |
| Boolean NOT | `(Stockholm NOT trolldom)` | Exclude term |
| Boosting | `Stockholm^4 trol*` | Increase relevance weight |
| Complex | `((troll* OR hax*) AND (Stockholm OR Goteborg))` | Combine operators |

## Best Practices

- **Wildcards for word variations**: `troll*` finds "trolldom", "trolleri", "trollkona"
- **Fuzzy for spelling variants**: `Stockholm~1` catches OCR misreads
- **Year filtering**: Use `year_min`/`year_max` to narrow time periods
- **Sorting**: `sort="timeAsc"` for earliest mentions, `sort="timeDesc"` for most recent
- **Metadata search**: Use dedicated `name` and `place` parameters in `search_metadata`
  for targeted person/place searches instead of putting everything in `keyword`

## Typical Workflow

1. **Comprehensive search**: `search_transcribed(term, 0)`, then offset=50, 100, etc.
2. **Search related terms** in parallel to build complete context
3. **Use advanced syntax** for precise queries (Boolean, wildcards, fuzzy, proximity)
4. **Review hit summaries** to identify most relevant documents across all searches
5. **Browse full pages** with `browse_document` for detailed examination

## Deep Dive: Proximity Search

For the full proximity search guide with working examples, troubleshooting tips,
and advanced layering strategy, see [references/solr-syntax.md](references/solr-syntax.md).
