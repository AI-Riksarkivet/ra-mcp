---
name: upload-files
description: >
  Upload local files or user attachments to the Gradio server and get back
  public URLs. Use when: upload image, upload XML, upload attachment,
  file to URL, host file, upload for HTR, upload for viewer, prepare files
  for transcription, upload document images.
---

# Upload Files

Upload local files or user-provided attachments (images, XML, etc.) to the
Gradio server so they become publicly accessible URLs. These URLs can then
be passed to tools like `htr_transcribe` or the document viewer.

## When to use

- User has attached images or XML files in the conversation
- User has local file paths that need to be accessible by a remote tool
- Any tool requires http/https URLs but you only have local data

If you already have http/https URLs (e.g. IIIF links, public image URLs),
skip this skill entirely and pass them directly to the target tool.

## Server URL

The upload target is the Gradio Space that backs the HTR MCP server:

```
https://riksarkivet-htr-demo.hf.space
```

Override with the `HTR_SPACE_URL` environment variable if set.

## Upload workflow

### Step 1: Save attachments to disk

If the user attached files in the conversation (not already on disk), save
them first. Claude attachments are available as content in the conversation
— write them to temporary files.

### Step 2: Upload each file

For each file, POST to the Gradio upload endpoint:

```bash
curl -s -X POST "https://riksarkivet-htr-demo.hf.space/gradio_api/upload" \
  -F "files=@/path/to/filename.jpg"
```

Response is a JSON array of server paths:

```json
["/tmp/gradio/abc123def/filename.jpg"]
```

### Step 3: Construct public URLs

For each server path returned, construct the public URL:

```
https://riksarkivet-htr-demo.hf.space/gradio_api/file=/tmp/gradio/abc123def/filename.jpg
```

Pattern: `{base_url}/gradio_api/file={server_path}`

### Step 4: Collect all URLs

Gather all constructed URLs before passing them to the target tool.
Present the URLs to the user so they can verify the uploads succeeded.

## Batch upload

You can upload multiple files in a single request:

```bash
curl -s -X POST "https://riksarkivet-htr-demo.hf.space/gradio_api/upload" \
  -F "files=@page1.jpg" \
  -F "files=@page2.jpg" \
  -F "files=@page3.jpg"
```

Response:

```json
[
  "/tmp/gradio/abc123/page1.jpg",
  "/tmp/gradio/abc123/page2.jpg",
  "/tmp/gradio/abc123/page3.jpg"
]
```

Prefer batch upload over individual uploads when possible.

## Supported file types

| Type | Extensions | Use with |
|------|-----------|----------|
| Images | `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff` | `htr_transcribe`, document viewer |
| ALTO XML | `.xml` | document viewer (text layer overlay) |
| PAGE XML | `.xml` | document viewer (text layer overlay) |

## After uploading

Once you have public URLs, pass them to the appropriate tool:

- **HTR transcription**: call `htr_transcribe` with `image_urls=[...]`
- **Document viewer**: call `view_document` with `image_urls=[...]` and optionally `text_layer_urls=[...]`

## Error handling

- **Connection error**: the Gradio Space may be sleeping. Retry after 30 seconds.
- **413 Payload Too Large**: file exceeds the server limit. Try uploading fewer files per request.
- **Empty response**: verify the file path is correct and the file exists.
