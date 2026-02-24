# Skills

Skills are loaded from the [ra-mcp-tools plugin](https://github.com/AI-Riksarkivet/ra-mcp/tree/main/plugins/ra-mcp-tools) and provide research methodology guidance. They are auto-discovered from `plugins/*/skills/` directories.

---

## /archive-search

Essential pre-search guide. Covers tool selection (`search_transcribed` vs `search_metadata`), Solr query syntax, wildcards, fuzzy matching for OCR/HTR errors, old Swedish spelling variants (präst/prest, silver/silfver), proximity search, Boolean operators, and pagination workflows.

## /archive-research

Research methodology guide. Covers research integrity rules (never fabricate data, always cite precisely), cross-tool research workflow (discover, examine, contextualize, synthesize), browsing strategy, result presentation with proper citations, and archive coverage awareness.

## /htr-transcription

HTR workflow guide. Covers the full pipeline: determine image source, batch images into a single `htr_transcribe` call, present results as an interactive artifact. Documents language options, layout modes, export formats, and custom HTRflow YAML pipelines.

## /view-document-guide

Document viewer guide. Covers the `view_document` tool's arguments, pairing rules, and common mistakes.

## /upload-files

File upload guide. Covers uploading local files or attachments to get public URLs for HTR or the viewer.
