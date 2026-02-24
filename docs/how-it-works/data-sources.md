# Data Sources & Coverage

ra-mcp connects to several Riksarkivet APIs:

| API | Endpoint | Purpose |
|-----|----------|---------|
| **Search API** | `data.riksarkivet.se/api/records` | Full-text search across transcribed documents |
| **ALTO XML** | `sok.riksarkivet.se/dokument/alto` | Structured page transcriptions with text coordinates |
| **IIIF** | `lbiiif.riksarkivet.se` | High-resolution document images and collection manifests |
| **OAI-PMH** | `oai-pmh.riksarkivet.se/OAI` | Document metadata and collection structure |
| **Bildvisaren** | `sok.riksarkivet.se/bildvisning` | Interactive image viewer (links provided in results) |

All data comes from the [Riksarkivet Data Platform](https://github.com/Riksarkivet/dataplattform/wiki), which hosts AI-transcribed materials from the Swedish National Archives.

Additional resources: [Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm) (semantic search, experimental), [HTRflow](https://pypi.org/project/htrflow/) (handwritten text recognition).

---

## Archive Coverage

The archive has three access tiers — not all materials are searchable the same way:

| Tier | Tool | Coverage |
|------|------|----------|
| **Metadata catalog** | `search_metadata` | 2M+ records — titles, names, places, dates |
| **Digitised images** | `browse_document` (links) | ~73M pages viewable via bildvisaren |
| **AI-transcribed text** | `search_transcribed` | ~1.6M pages — currently court records (hovrätt, trolldomskommissionen, poliskammare, magistrat) from 17th-18th centuries |

Church records, estate inventories, and military records are typically cataloged and often digitised, but NOT AI-transcribed.

## Transcription Quality

The AI-transcribed text was produced by HTR (Handwritten Text Recognition) and OCR models. These transcriptions are **not perfect** — they contain recognition errors including misread characters, merged or split words, and garbled passages, especially in older or damaged documents.

This has a direct impact on search: an exact search for `Stockholm` will miss documents where the transcription reads `Stockholn` or `Stookholm` due to recognition errors. **Always use fuzzy search (`~`)** to compensate — `stockholm~1` catches common misreads and significantly increases the number of hits.

## The Plugin Model

ra-mcp is one piece of a larger ecosystem. Multiple MCP servers can be connected to the same AI client:

``` mermaid
graph LR
  client["AI Client\n(Claude)"]
  client --> ramcp["ra-mcp\nSearch, browse, HTR, viewer, guides"]
  client --> htrflow["htrflow-mcp\nStandalone HTR\n(alternative)"]
  client --> other["other servers\nAny MCP-compatible tool"]
```

Together with external tools, they enable a complete research workflow: search the archives, read transcriptions, re-transcribe pages that need better OCR/HTR, and view original documents — all from within a single AI conversation.
