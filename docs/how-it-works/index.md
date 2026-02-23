---
icon: lucide/cog
---

# How it Works

ra-mcp uses the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) to give AI assistants direct access to the Swedish National Archives. Instead of the AI guessing about historical documents, it can search and read them in real time.

---

## What is MCP?

MCP is an open protocol that lets AI models call external tools. Think of it like a USB port for AI — any model that speaks MCP can plug into any MCP server and use its tools.

``` mermaid
graph LR
  A["AI Client\n(Claude, ChatGPT, etc)"] <-->|"MCP\ntool calls"| B["ra-mcp Server"]
  B --> C["Riksarkivet\nData Platform\n(Search, IIIF, ALTO, OAI-PMH)"]
  B --> D["HTRflow\nGradio Space\n(Handwritten text recognition)"]
```

When you ask Claude *"Find documents about trolldom"*, the AI:

1. Recognizes it needs to search historical archives
2. Calls the `search_transcribed` tool via MCP
3. ra-mcp queries the Riksarkivet Search API
4. Results come back through MCP to the AI
5. The AI presents them to you with context and analysis

## The Tools

### search_transcribed

Searches AI-transcribed text across millions of digitised historical document pages. Supports advanced Solr query syntax including wildcards, fuzzy matching, boolean operators, proximity searches, and date filtering.

**Example query flow:**

```
User: "Find 17th century court records mentioning trolldom near Stockholm"

AI calls: search_transcribed(
    keyword='("Stockholm trolldom"~10)',
    offset=0,
    year_min=1600,
    year_max=1699,
    sort="timeAsc"
)
```

### search_metadata

Searches document metadata fields — titles, personal names, place names, archival descriptions, and provenance. Covers 2M+ records. Useful for finding specific archives, people, or locations.

### browse_document

Retrieves complete page transcriptions from a specific document. Each result includes the full transcribed text and direct links to the original page images in Riksarkivet's image viewer.

### htr_transcribe

Transcribes handwritten document images using AI-powered handwritten text recognition (HTRflow). Accepts image URLs and returns an interactive viewer, per-page transcription data, and archival exports in ALTO XML, PAGE XML, or JSON. Supports Swedish, Norwegian, English, and medieval documents.

### view_document

Displays document pages in an interactive viewer with zoomable images and text layer overlays. The viewer runs directly inside the MCP host (Claude, ChatGPT) as an MCP App.

See [Tools & Skills](../tools/index.md) for full parameter documentation.

## Data Sources

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

## Archive Coverage

The archive has three access tiers — not all materials are searchable the same way:

| Tier | Tool | Coverage |
|------|------|----------|
| **Metadata catalog** | `search_metadata` | 2M+ records — titles, names, places, dates |
| **Digitised images** | `browse_document` (links) | ~73M pages viewable via bildvisaren |
| **AI-transcribed text** | `search_transcribed` | ~1.6M pages — currently court records (hovrätt, trolldomskommissionen, poliskammare, magistrat) from 17th-18th centuries |

Church records, estate inventories, and military records are typically cataloged and often digitised, but NOT AI-transcribed.

### Transcription Quality

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

See [Getting Started](../getting-started/index.md) for setup instructions, or [Architecture](../architecture/index.md) for the full package structure.
