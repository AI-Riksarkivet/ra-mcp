---
name: feedback-ls
description: >
  Guide for sending document pages to Label Studio for human feedback on transcriptions.
  Use when: feedback, label studio, annotation, review transcription, quality check,
  send to label studio, import to label studio, human review, correct transcription,
  segmentation feedback, transcription feedback, ALTO to label studio,
  review pages, flag pages for review, quality assurance, QA, annotation task,
  annotate images, label images, send images for annotation.
---

# Label Studio Feedback Workflow

Send document pages to Label Studio for human annotation and feedback.

## Tool

- `label_import_to_label_studio` — Import pages to a Label Studio project.
  Two modes:
  - **With ALTO**: pre-annotated tasks with polygons and transcriptions
  - **Images only**: blank tasks for annotation from scratch

## When to Use

- User asks to send pages for human review or annotation
- User wants to flag transcription or segmentation issues
- User wants to create Label Studio tasks from browse results
- User wants to send images for annotation from scratch
- User asks for quality assurance on specific pages

## Two Modes

### Mode 1: Pre-annotated (with ALTO XML)

Use when pages already have AI transcriptions. The tool fetches ALTO XML,
extracts text line polygons and transcriptions, and creates VectorLabels
pre-annotations.

```json
{
  "image_urls": [
    "https://lbiiif.riksarkivet.se/arkis!30002056_00004/full/max/0/default.jpg"
  ],
  "alto_urls": [
    "https://sok.riksarkivet.se/dokument/alto/SE_RA_30002056_00004"
  ],
  "feedback": [["Transcription"]]
}
```

### Mode 2: Images only (no ALTO)

Use when there are no existing transcriptions — the user wants to annotate
from scratch. Just pass image URLs, omit `alto_urls`.

```json
{
  "image_urls": [
    "https://lbiiif.riksarkivet.se/arkis!30002056_00004/full/max/0/default.jpg",
    "https://lbiiif.riksarkivet.se/arkis!30002056_00005/full/max/0/default.jpg"
  ]
}
```

## Choosing the Right Source for Pre-annotations

When the user wants to send pages with pre-annotations, choose the source
based on what's available:

| Situation | Source | How |
|-----------|--------|-----|
| Pages from `browse_document` results | ALTO XML from Riksarkivet | Pass `alto_urls` from browse output |
| User has images without transcriptions | No pre-annotations | Omit `alto_urls` (image-only mode) |
| User has images and wants AI transcription first | HTR transcription | Use `htr_transcribe` first to generate ALTO XML, then pass the ALTO export URLs as `alto_urls` |
| User wants to label/annotate themselves | No pre-annotations | Omit `alto_urls` — blank tasks for manual annotation |

**Tip**: If the user has untranscribed images and wants pre-annotations, suggest
running `htr_transcribe` (see `/htr-transcription` skill) first to generate
ALTO XML, then feed those results into this tool.

## Workflow

### 1. Get page URLs

**From browse results**: Call `browse_browse_document` first (or use results
already in the conversation). Each page includes:

- **ALTO XML URL**: `https://sok.riksarkivet.se/dokument/alto/...`
- **Image URL**: `https://lbiiif.riksarkivet.se/arkis!.../full/max/0/default.jpg`

**From any image source**: Any publicly accessible image URL works for
image-only mode.

### 2. Determine feedback choices (optional, ALTO mode only)

| Value | Meaning |
|-------|---------|
| `Transcription` | Text recognition needs correction |
| `Segmentation` | Line/region boundaries need correction |

Each page gets its own list of feedback values. Use an empty list `[]` for pages
that need general review without a specific feedback flag.

### 3. Call the tool

Label Studio URL, token, and project ID are configured via environment variables
(`LS_URL`, `LS_TOKEN`, `LS_PROJECT_ID`) — no need to pass them unless overriding.

### 4. Confirm to the user

Report back the number of tasks imported, the mode (pre-annotated or image-only),
and the project they were sent to.

## Dry Run — Preview Before Import

Set `dry_run=true` to see the converted Label Studio JSON without importing.

```json
{
  "image_urls": ["..."],
  "alto_urls": ["..."],
  "dry_run": true
}
```

## Pairing Rules

When using `alto_urls`, all lists are paired by index — `alto_urls[i]`,
`image_urls[i]`, and `feedback[i]` refer to the same page.

| Rule | Detail |
|------|--------|
| `image_urls` is always required | One image URL per page |
| `alto_urls` is optional | Omit for image-only tasks |
| `alto_urls` and `image_urls` must match length | One ALTO XML per image |
| `feedback` must match length if provided | One feedback list per page |
| `feedback` requires `alto_urls` | Feedback choices attach to ALTO text regions |

## Extracting URLs from Browse Results

The `browse_browse_document` tool returns per-page links in this format:

```
🔗 Links:
  📝 ALTO XML: https://sok.riksarkivet.se/dokument/alto/SE_RA_30002056_00004
  🖼️  Image: https://lbiiif.riksarkivet.se/arkis!30002056_00004/full/max/0/default.jpg
```

Collect the `Image` URLs (always needed) and `ALTO XML` URLs (only if you
want pre-annotations).

## Batch Strategy

- **Small sets (1-10 pages)**: Send all pages in a single call.
- **Larger sets**: Batch into groups of 10-20 pages per call to avoid timeouts.
  The tool has a 120-second timeout.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Mismatched list lengths | `alto_urls` and `image_urls` must be the same length |
| Passing feedback without alto_urls | Feedback requires ALTO (choices attach to text regions) |
| Passing feedback as flat list | Each entry must be a **list of strings**, e.g. `[["Transcription"], []]` not `["Transcription", ""]` |
| Wrong ALTO URL format | Use the full URL from browse results, not just the page ID |
| Passing Label Studio credentials | Credentials are loaded from env vars — only pass if overriding |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LS_URL` | Label Studio instance URL |
| `LS_TOKEN` | Label Studio Personal Access Token (JWT PAT) |
| `LS_PROJECT_ID` | Target project ID |

These are configured in `packages/label-mcp/.env` and loaded automatically.
