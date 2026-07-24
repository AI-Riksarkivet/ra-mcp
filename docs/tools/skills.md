# Skills

Skills are short guides that teach the AI assistant *how* to use the ra-mcp tools well — search strategy, citation rules, the transcription workflow, and so on. They ship as a Claude Code **plugin** called `ra-mcp-tools`, and once installed the assistant uses them automatically whenever they're relevant.

> Skills are **guidance only** — they don't add tools. The tools themselves come from the ra-mcp MCP server (see [Getting Started](../getting-started/index.md)). Skills just make the assistant use those tools well.

## Install the skills (Claude Code)

You need **Claude Code v2.1.143 or newer** — check with `claude --version`, and update with `npm install -g @anthropic-ai/claude-code@latest` if needed. Then paste these three commands, one at a time:

```
/plugin marketplace add AI-Riksarkivet/ra-mcp
/plugin install ra-mcp-tools@ra-mcp-plugins
/reload-plugins
```

1. **`/plugin marketplace add …`** registers this repository as a plugin source (it reads `.claude-plugin/marketplace.json` automatically). Nothing is installed yet — this just adds the catalogue.
2. **`/plugin install ra-mcp-tools@ra-mcp-plugins`** installs the skills. When prompted for a scope, choose **User** to have them in every project.
3. **`/reload-plugins`** activates them without restarting Claude Code.

To confirm, run `/help` and look under **Custom Agents and Skills** — the eight `ra-mcp-tools` skills should be listed.

## How the skills are used

- **Automatically (the normal way):** the assistant loads the right skill on its own based on what you ask — e.g. asking it to search the archives triggers `/archive-search`. You don't have to type anything.
- **Manually:** you can force a specific one by typing its name, e.g. `/ra-mcp-tools:archive-search`.

## On claude.ai and other MCP clients

If you use ra-mcp on **claude.ai** (or any MCP client that isn't Claude Code), you **don't install anything separately** — just [connect the ra-mcp MCP server](../getting-started/index.md#connect-to-claudeai). The server publishes these same skills as **MCP resources**, so the assistant can consult them while it works. The `/plugin` steps above are **only** for Claude Code, where they become auto-invoked Claude Code skills.

| Client | How you get the skills |
|--------|------------------------|
| **claude.ai** (web) | Automatic — connect the MCP server; skills arrive as MCP resources. No install. |
| **Claude Desktop / VS Code / Cursor** | Automatic — same as claude.ai, via the connected MCP server. |
| **Claude Code (CLI)** | Install the `ra-mcp-tools` plugin (the `/plugin` steps above) for auto-invoked skills. |

## The eight skills

---

## /archive-search

Essential pre-search guide — load before calling `search_transcribed` or `search_metadata`. Covers tool selection (`search_transcribed` vs `search_metadata`), search strategy, the verified query syntax (implicit AND between terms, wildcards, fuzzy, exact phrases — no boolean operators), fuzzy matching for OCR/HTR errors, old Swedish spelling variants (präst/prest, silver/silfver), and pagination workflows.

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
