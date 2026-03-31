ARG BASE_IMAGE=python:3.13-slim
ARG BUILDER_IMAGE=${BASE_IMAGE}
ARG PRODUCTION_IMAGE=${BASE_IMAGE}

# --- Stage 1: Build viewer-mcp frontend (Svelte/Vite) ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY packages/viewer-mcp/package*.json ./
RUN npm ci
COPY packages/viewer-mcp/tsconfig.json packages/viewer-mcp/vite.config.ts packages/viewer-mcp/mcp-app.html ./
COPY packages/viewer-mcp/ui ./ui
RUN npm run build

# --- Stage 2: Build Python workspace with uv ---
FROM ${BUILDER_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /usr/local/bin/uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1
WORKDIR /app

# Copy workspace configuration and all packages
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY src/ ./src/
COPY README.md LICENSE ./

# Copy built frontend into viewer-mcp package before uv sync
# vite outputs to src/ra_mcp_viewer_mcp/dist/, so --no-editable will include it in the wheel
COPY --from=frontend-builder /app/src/ra_mcp_viewer_mcp/dist/ ./packages/viewer-mcp/src/ra_mcp_viewer_mcp/dist/

# Sync workspace packages with diplomatics extra (--no-editable makes .venv self-contained)
RUN uv sync --frozen --no-cache --no-dev --no-editable --extra diplomatics

# Build LanceDB tables (downloads CSVs from upstream)
COPY scripts/ ./scripts/
RUN uv run python scripts/ingest_diplomatics.py --output /app/data/diplomatics

# --- Stage 3: Production runtime ---
FROM ${PRODUCTION_IMAGE} AS production

# Install runtime dependencies based on base image
# Alpine uses apk, Wolfi/Chainguard use apk, Debian uses apt
RUN if command -v apk >/dev/null 2>&1; then \
        apk upgrade --no-cache && \
        apk add --no-cache ca-certificates libgcc; \
    elif command -v apt-get >/dev/null 2>&1; then \
        apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y --no-install-recommends ca-certificates && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Remove pip and setuptools to eliminate CVE-2025-8869 and CVE-2026-1703
# We use uv for all package management, so pip is not needed at runtime
# Use rm -rf directly instead of invoking pip to avoid executing a potentially vulnerable binary
RUN rm -rf /usr/local/lib/python3.13/site-packages/pip* \
           /usr/local/lib/python3.13/site-packages/setuptools* \
           /usr/local/lib/python3.13/site-packages/wheel* \
           /usr/local/bin/pip* 2>/dev/null || true

# Create non-root user for security (works on both Alpine and Debian)
RUN if command -v addgroup >/dev/null 2>&1 && command -v adduser >/dev/null 2>&1; then \
        addgroup --gid 1000 ra-mcp && \
        adduser --uid 1000 --ingroup ra-mcp --disabled-password --gecos "" ra-mcp; \
    else \
        groupadd -g 1000 ra-mcp && \
        useradd -u 1000 -g ra-mcp -s /bin/sh -m ra-mcp; \
    fi

WORKDIR /app

# Copy only what's needed at runtime (--chown avoids a separate chown layer)
# With --no-editable, .venv is self-contained — no need to copy src/ or packages/
COPY --from=builder --chown=ra-mcp:ra-mcp /app/.venv /app/.venv
COPY --chown=ra-mcp:ra-mcp docs/assets/ ./docs/assets/
COPY --chown=ra-mcp:ra-mcp packages/guide-mcp/resources/ ./resources/
COPY --chown=ra-mcp:ra-mcp plugins/ ./plugins/
COPY --from=builder --chown=ra-mcp:ra-mcp /app/data/diplomatics/ ./data/diplomatics/

RUN mkdir -p /app/data && chown ra-mcp:ra-mcp /app /app/data

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV DIPLOMATICS_LANCEDB_PATH="/app/data/diplomatics"

# Health check via /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:7860/health')" || exit 1

EXPOSE 7860
CMD ["ra-serve", "--http", "--host", "0.0.0.0", "--port", "7860"]
