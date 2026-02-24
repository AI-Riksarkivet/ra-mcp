# Deployment

ra-mcp can be deployed as a Docker container, via Helm, or on Hugging Face Spaces.

---

## Docker

```bash
docker run -p 7860:7860 riksarkivet/ra-mcp:latest
```

Available image variants:

| Tag suffix | Base image | Notes |
|------------|-----------|-------|
| `-alpine` | `python:3.13-alpine` | Lightweight (default) |
| `-wolfi` | `cgr.dev/chainguard/python:latest-dev` | Minimal CVEs |
| `-slim` | `python:3.13-slim` | Debian slim |

## Docker Compose (via Dagger)

```bash
# Start server (exposed on host port 7860)
dagger call compose-up up --ports 7860:7860

# Run health check
dagger call compose-test
```

## Connect to Claude Code

```bash
# 1. Start the server
dagger call compose-up up --ports 7860:7860

# 2. Add as MCP server
claude mcp add --transport http ra-mcp http://localhost:7860/mcp

# 3. Verify
/mcp
```

## Helm

```bash
helm install ra-mcp charts/ra-mcp \
  --set image.tag=v0.8.0-alpine \
  --set opentelemetry.enabled=true
```

See [charts/ra-mcp/](https://github.com/AI-Riksarkivet/ra-mcp/tree/main/charts/ra-mcp) for the full values reference (autoscaling, ingress, PDB, security contexts).

## Hugging Face Spaces

The hosted instance runs at:

```
https://riksarkivet-ra-mcp.hf.space/mcp
```

## Health Endpoints

Available when running with HTTP transport:

| Endpoint | Purpose |
|----------|---------|
| `/health` | Liveness — always returns `{"status": "ok"}` |
| `/ready` | Readiness — returns mounted modules or 503 if none loaded |

```bash
curl http://localhost:7860/health
curl http://localhost:7860/ready
```
