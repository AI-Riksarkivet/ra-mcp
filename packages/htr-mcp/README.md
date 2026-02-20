# ra-mcp-htr-mcp

MCP tool for handwritten text recognition (HTR) via a remote Gradio Space.

## Usage

This package provides an `htr_transcribe` MCP tool that delegates to a remote
[HTRflow Gradio Space](https://huggingface.co/spaces/Riksarkivet/htr-demo) using
`gradio_client.Client`.

### Standalone

```bash
# stdio transport
python -m ra_mcp_htr_mcp.server --stdio

# HTTP transport
python -m ra_mcp_htr_mcp.server --port 3002
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `HTR_SPACE_URL` | `https://riksarkivet-htr-demo.hf.space` | Gradio Space URL |

### As part of the composed server

The tool is automatically available when the `htr` module is enabled in the
root `ra-mcp` server (enabled by default).
