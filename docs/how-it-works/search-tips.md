# Search Tips

Transcriptions in Riksarkivet are **AI-generated** (HTR/OCR) from **historical**
handwritten documents. Two facts about that material change search results
dramatically, and neither is obvious to newcomers:

1. Historical documents use **historical place and administrative names**, not modern ones.
2. HTR misreads old handwriting, so the **same word appears in many spellings**.

Both apply to the CLI (`ra search`), the MCP `transcribed` tool, and any agent
driving them.

## Use historical place names

Searching for a region by its modern name misses most of the record, because the
documents predate the modern name. County (*län*) names in particular changed in
1997. In our testing the historical county name returns roughly **10× more hits**
than the modern region name:

| You want… | Search instead for | Why |
|-----------|--------------------|-----|
| Dalarna | `Kopparbergs~1` | *Kopparbergs län*, used until 1997 |
| Västra Götaland | `Skaraborgs`, `Älvsborgs`, `Bohus` — one search each | Merged from three older *län* in 1998 |
| Skåne | `Malmöhus`, then `Kristianstads` | Merged in 1997 |

Rough rule for administrative names: **before 1634** think *landskap*, **1634–1997**
think *län*, **after 1997** think *regioner*. When in doubt, search the older name.

## Use fuzzy search (`~1`) for HTR variants

Because transcriptions are machine-read from old handwriting, an exact search
misses every misread spelling. Adding `~1` (fuzzy match, edit-distance 1) catches
them. For "Leksand", fuzzy search returns **~85% more hits** than exact:

```
"Leksand"    → 214 total hits
"Leksand~1"  → 397 total hits   (+85%)
"leksand~1"  → 397 total hits   (case-insensitive)
```

All of the following real HTR spellings of "Leksand" are found **only** with
fuzzy search:

| Variant | Example context |
|---------|-----------------|
| laksand | "Bonden Erich Olßon i laksand" |
| Laksands | "Fjerdingen i Laksands Socken" |
| leksandz | "Åker och leksandz Sochn" |
| Leksandt | "Leksandt Bräder" |
| Lexsand | "sedel til Lexsand å 20 tolfter" |
| Lecksand | "dett slut uti Lecksand" |
| Lehsands | "Lehsands Ahls och Bjurås tingsrätt" |
| Liksands | "Liksands Sohns HäradsRätt" |
| Lekands | "wid Lekands Åhls och Bjursårs" |

Fuzzy search does admit some false positives (`lekande` = "playing", `lesande` =
"reading") — an inherent trade-off. For broad recall on any name or place,
**default to `~1`** and skim; for precision, drop it.

The same idea covers spelling reforms even without HTR error, e.g. `präst`/`prest`,
`silver`/`silfver`. A single fuzzy or wildcard term often covers both (`präst~1`,
`silf*`); otherwise run one search per variant — the API has no OR operator
(`AND`/`OR`/`NOT` are matched as literal words and such queries are rejected).

## Combining the two

The techniques stack: space-separated terms are all required (implicit AND), so
add terms to narrow. To sweep Dalarna church records broadly, one search per
region variant:

```bash
ra search "Kopparbergs~1 kyrka~1"
ra search "Kopparbergs~1 socken~1"
ra search "Dalarna kyrka~1"
```

See [`ra search`](../cli/search.md) for the full flag reference, and
[Data Sources](data-sources.md) for where this material comes from.
