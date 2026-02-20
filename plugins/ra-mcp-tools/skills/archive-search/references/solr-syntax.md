# Solr Proximity Search Reference

Complete guide to proximity search in the Riksarkivet search tools.

## Proximity Search Rules

Proximity search finds two terms within a specified word distance of each other.

### Quote Rules

Always wrap both terms in quotes:

```
"term1 term2"~N    correct
term1 term2~N      wrong — will not work
```

### Two-Term Limit

Only 2 terms work reliably in a proximity phrase:

```
"kyrka stold"~10           correct
"kyrka silver stold"~10    wrong — unreliable with 3+ terms
```

### Distance Notation

The `~N` suffix specifies maximum word distance:

- `~3` = within 3 words (tight proximity)
- `~10` = within 10 words (paragraph-level)
- `~50` = within 50 words (page-level)

## Working Examples by Category

### Crime & Punishment

```
"tredje stold"~5           # Third-time theft
"domd hanga"~10            # Sentenced to hang
"inbrott natt*"~5          # Burglary at night
"kyrka stold"~10           # Church theft
```

### Values & Items

```
"hundra daler"~3           # Hundred dalers
"stor* stold*"~5           # Major theft
"guld* ring*"~10           # Gold ring
"silver* kalk*"~10         # Silver chalice
```

### Complex Combinations

Combine proximity searches with Boolean operators outside the quotes:

```
("kyrka stold"~10 OR "kyrka tjuv*"~10) AND 17*
# Church thefts or church thieves in 1700s

("inbrott natt*"~5) AND (guld* OR silver*)
# Night burglaries involving gold or silver

("forsta resan" AND stold*) OR ("tredje stold"~5)
# First-time theft OR third theft (within proximity)
```

## Troubleshooting

If proximity search returns no results:

1. **Check your quotes** — must wrap both terms in `"..."`
2. **Reduce to 2 terms** — drop extra words from the phrase
3. **Try exact terms first** — before adding wildcards
4. **Increase distance** — try `~10` instead of `~3`
5. **Simplify wildcards** — use wildcard on one term only

## Advanced Strategy: Layering Searches

Build from simple to complex, verifying results at each step:

```
Step 1: "kyrka stold"~10
Step 2: ("kyrka stold"~10 OR "kyrka tjuv*"~10)
Step 3: (("kyrka stold"~10 OR "kyrka tjuv*"~10) AND 17*)
Step 4: (("kyrka stold"~10 OR "kyrka tjuv*"~10) AND 17*) AND (guld* OR silver*)
```

## Most Reliable Proximity Patterns

| Pattern | Example | Reliability |
|---------|---------|-------------|
| Exact + Exact | `"hundra daler"~3` | Most reliable |
| Exact + Wildcard | `"inbrott natt*"~5` | Reliable |
| Wildcard + Wildcard | `"stor* stold*"~5` | Sometimes works |

The key insight: proximity operators work best with exactly 2 terms in quotes.
Combine multiple proximity searches using Boolean operators *outside* the quotes.
