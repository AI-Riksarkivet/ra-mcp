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

