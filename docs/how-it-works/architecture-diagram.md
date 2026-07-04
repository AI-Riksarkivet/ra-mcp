# Search & viewers — interactive diagram

This page explains, in plain terms, how the Riksarkivet MCP server fits together —
one server, **two separate viewers**, and **four different searches**. The interactive
version is [`architecture.html`](architecture.html) (open it in a browser and click
through each flow); this page is the same story in text. For the full package/layer
reference, see [Architecture](architecture.md).

> **The one thing to remember:** **LanceDB is used for *text search only*.** Images,
> ALTO polygons, PDFs, and all rendering never go through LanceDB. Searching for a word
> and *showing* you a document are two completely different jobs.

## The pieces

| Piece | What it is |
|---|---|
| **Claude (client)** | The AI assistant. It calls *tools* on the server. |
| **FastMCP server** | One server that *composes* (mounts) all the modules and routes each tool call to the right one. |
| **search-mcp** | The **live** archive search — `search_transcribed` / `search_metadata`. |
| **13 dataset MCPs** | Curated datasets (sbl, court, dds, …), each a searchable local collection. |
| **pdf-mcp** | The **PDF viewer** (PDF.js) *and* the guide search (`search_guides` / `search_pdf`). |
| **viewer-mcp** | The **document viewer** — IIIF scans with an ALTO text-layer overlay, drawn on a `<canvas>`. |
| **dataset-lib spine** | `ra-mcp-dataset-lib` — one shared Swedish full-text search used by all datasets *and* the guide search. |
| **Local LanceDB** | On-disk (datasets) / in-memory (guides) full-text indexes. |
| **Riksarkivet Solr API** | The remote archive API (~1.6M transcribed pages). Not local. |
| **IIIF · ALTO · HF PDF** | The media the viewers render: page images, text-layer XML, and PDF bytes. |

## Two viewers — and why they're separate

- **`viewer-mcp`** renders photographic **scans** (IIIF images) with a **transcription overlay** (ALTO line polygons) on a custom `<canvas>`.
- **`pdf-mcp`** renders **born-digital PDFs** with **PDF.js**.

They're separate MCP Apps with separate `ui://` resources because the rendering engines have nothing in common — merging them would make one bloated app that does both jobs badly.

## Four searches — and what backs each

1. **Live archive search** (`search_transcribed` / `search_metadata`) → the **remote Riksarkivet Solr API**. This is the big archive; nothing local.
2. **Dataset search** (the 13 dataset tools) → the **shared spine → local LanceDB** (Swedish FTS, BM25). Offline, fast, ranked.
3. **PDF guide search** (`search_guides` / `search_pdf`) → the **same spine → LanceDB** over the guides' text blocks. So guide search gets the *same* Swedish stemming + ranking as the datasets (`kung` matches `kungar`/`kungens`), and each matched block keeps its bounding box so the PDF viewer can highlight it.
4. **In-document find** (the viewer's page search) → scans the **ALTO text of the page you're already viewing** to highlight a word. It's a highlight, not a corpus search — so it does *not* use LanceDB.

## The five flows (in the interactive diagram)

1. **Live archive search** — `Claude → server → search-mcp → Solr API → back`. Remote HTTP; no LanceDB.
2. **Dataset search (LanceDB)** — `Claude → server → dataset-mcp → spine → local LanceDB → back`. The blocking search runs off the event loop in a worker thread; the spine adds Swedish stemming, a real total, stable pagination, and a pushed-down `.where()` filter.
3. **PDF guide search (LanceDB)** — `Claude → server → pdf-mcp → same spine → LanceDB → back`. Shows the guide search reusing the dataset spine.
4. **Open document viewer** — `Claude → server → viewer-mcp → IIIF images + ALTO XML → canvas`. Pure rendering; **no LanceDB**. Images are decoded off the paint path and the ALTO overlays are idle-gated for smooth pan/zoom.
5. **Open PDF viewer** — `Claude → server → pdf-mcp → HF PDF bytes → PDF.js`. A separate app from the document viewer; **no LanceDB**. `search_guides` (flow 3) highlights its matches here.

## Where LanceDB is — and isn't

- **Is:** dataset search, PDF guide search (both via the shared spine). That's it — *text search*.
- **Isn't:** page images, ALTO polygons, PDF bytes, and all viewer/PDF.js rendering. Those are IIIF/HTTP/canvas concerns. Putting images or a render pipeline in a full-text index would be an anti-pattern.
