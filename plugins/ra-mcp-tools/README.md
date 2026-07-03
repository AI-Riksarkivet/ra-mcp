# Riksarkivet Tools Plugin for Claude Code

A Claude Code plugin providing skills for archive research workflows — search strategy, research methodology, archival record knowledge, HTR transcription, document and PDF viewing, Label Studio feedback, and file uploads.

## Installation

Install via Claude Code:

```
/install-plugin AI-Riksarkivet/ra-mcp plugins/ra-mcp-tools
```

## Skills

### `/archive-search`

Essential pre-search guide. Covers tool selection (`search_transcribed` vs `search_metadata`), Solr query syntax, wildcards, fuzzy matching for OCR/HTR errors, old Swedish spelling variants (präst/prest, silver/silfver), proximity search, Boolean operators, and pagination workflows.

**Trigger phrases**: search, find, look up, discover, query, search archives, find person, find place, trolldom, bouppteckning, dombok

### `/archive-research`

Research methodology guide. Covers research integrity rules (never fabricate data, always cite precisely), cross-tool research workflow (discover → examine → contextualize → synthesize), browsing strategy, result presentation templates with proper citations, and coverage awareness across the archive's three access tiers.

**Trigger phrases**: browse document, read pages, translate old Swedish, cite sources, present findings, research methodology

### `/archival-guide`

Swedish archival record-type and administrative-history guide. Maps research topics to the correct *Förvaltningshistorik* chapters (served as MCP resources) so you know what record types exist, which authorities created them, and where to find them — court records, church records, folkbokföring, bouppteckning, dombok, husförhörslängd, mantalslängd, military, tax, and prison records.

**Trigger phrases**: what records exist, which archive, document types, court records, church records, folkbokföring, bouppteckning, dombok, husförhörslängd, mantalslängd, Swedish administrative history

### `/htr-transcription`

HTR workflow guide. Covers the full pipeline: determine image source, batch all images into a single `htr_transcribe` call, present results as an inline artifact with the interactive viewer. Documents language options (Swedish, Norwegian, English, medieval), layout modes, export formats (ALTO XML, PAGE XML, JSON), and custom HTRflow YAML pipelines.

**Trigger phrases**: transcribe handwriting, HTR, handwritten document, OCR historical document, digitize manuscript

### `/view-document-guide`

Document viewer guide. Covers the three viewer entry points and how to choose between them: `view_document` (when you have a Riksarkivet reference code), `view_manifest` (when you have a IIIF manifest URL, e.g. from SDHK/MPO search), and `view_document_urls` (when you already have raw image and text-layer XML URLs).

**Trigger phrases**: view document, display pages, show document, document viewer, view manifest

### `/pdf-guide`

Riksarkivet PDF guide reader. Covers searching and reading the archival PDF guides (medieval Sweden, governance 1520–1920, Sami history) via `search_guides`, `read_pdf_page`, `display_pdf`, and `search_pdf`, returning section-level references with page numbers for citation.

**Trigger phrases**: Swedish history, archives, medieval charters, governance, Sami, open PDF guide, search PDF guides

### `/feedback-ls`

Label Studio feedback workflow. Covers sending document pages to Label Studio for human annotation via `import_to_label_studio` — both ALTO pre-annotated tasks and image-only blank tasks, with transcription/segmentation feedback choices and optional assignment.

**Trigger phrases**: feedback, label studio, annotation, review transcription, quality check, human review, segmentation feedback, transcription feedback

### `/upload-files`

File upload guide. Covers uploading local files or user attachments to the Gradio server to get public URLs for use with `htr_transcribe` or the document viewer. Documents the upload workflow, batch uploads, supported file types, and error handling.

**Trigger phrases**: upload image, upload file, file to URL, upload for HTR

## How Skills Work

Skills are loaded as MCP resources via FastMCP's `SkillsDirectoryProvider`. The root server discovers skill directories from `plugins/*/skills/` at startup. Each skill is a `SKILL.md` file with YAML frontmatter (name, description) and markdown content.

## Adding a New Skill

1. Create a directory under `plugins/ra-mcp-tools/skills/{skill-name}/`
2. Add a `SKILL.md` file with frontmatter:

```markdown
---
name: my-skill
description: >
  When to use this skill and what it covers.
  Use when: trigger phrase 1, trigger phrase 2.
---

# My Skill

Content here...
```

3. The skill is auto-discovered on server restart.

## Part of ra-mcp

See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.
