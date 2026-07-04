# Skills

Skills are loaded from the [ra-mcp-tools plugin](https://github.com/AI-Riksarkivet/ra-mcp/tree/main/plugins/ra-mcp-tools) and provide research methodology guidance. They are auto-discovered from `plugins/*/skills/` directories. There are eight skills.

---

## /archive-search

Essential pre-search guide — load before calling `search_transcribed` or `search_metadata`. Covers tool selection (`search_transcribed` vs `search_metadata`), search strategy, Solr query syntax, wildcards, fuzzy matching for OCR/HTR errors, old Swedish spelling variants (präst/prest, silver/silfver), proximity search, Boolean operators, and pagination workflows.

## /archive-research

Essential research guide — load before browsing, reading, or presenting archival documents. Covers research integrity rules (never fabricate data, always cite precisely), citing sources with reference codes, translating old Swedish, the cross-tool research workflow (search, browse, synthesize), browsing strategy, result presentation, and coverage awareness.

## /archival-guide

Archival record-type and administrative-history guide. Maps a research topic (court records, church records, folkbokföring, bouppteckning, dombok, husförhörslängd, mantalslängd, military, tax, and prison records) to the correct Förvaltningshistorik chapters, which are available as MCP resources. Use when figuring out what records exist, which archive holds them, or how the archival structure works.

## /htr-transcription

HTR workflow guide. Covers the full pipeline: determine the image source, batch images into a single `htr_transcribe` call, and present results as an interactive artifact. Documents language options, layout modes, export formats, and custom HTRflow YAML pipelines.

## /view-document-guide

Document viewer guide. Covers the viewer tools' arguments, pairing rules, and common mistakes across the reference-code, IIIF-manifest, and raw-URL entry points (`view_document`, `view_manifest`, `view_bild`).

## /pdf-guide

PDF guide for Riksarkivet's bundled archival PDFs (medieval Sweden, governance 1520–1920, Sami history). Use when the user asks about Swedish history, archives, medieval charters, governance, or Sami history, or wants to open/search the PDF guides. Provides section-level references with page numbers for citation.

## /upload-files

File upload guide. Covers uploading local files or user attachments to the Gradio server to get back public URLs for HTR or the viewer.

## /feedback-ls

Label Studio feedback guide. Covers sending document pages (with ALTO transcriptions) to a Label Studio project for human review, transcription correction, and segmentation/quality feedback via the `label_import_to_label_studio` tool.
