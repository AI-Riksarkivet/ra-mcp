ARG BASE_IMAGE=python:3.13-slim
ARG BUILDER_IMAGE=${BASE_IMAGE}
ARG PRODUCTION_IMAGE=${BASE_IMAGE}

# --- Stage 1: Build BOTH MCP App frontends (Svelte/Vite): viewer + pdf ---
# Both must be built here — each vite build emits src/<pkg>/dist/mcp-app.html, which the
# wheel picks up (tool.hatch.build artifacts). Omitting either makes that App's ui:// resource
# 500 at runtime (FileNotFoundError). Keep this in lockstep with `make build-ui`.
FROM node:22-alpine AS frontend-builder

# viewer-mcp UI -> /viewer/src/ra_mcp_viewer_mcp/dist
WORKDIR /viewer
COPY packages/mcps/viewer-mcp/package*.json ./
RUN npm ci
COPY packages/mcps/viewer-mcp/tsconfig.json packages/mcps/viewer-mcp/vite.config.ts packages/mcps/viewer-mcp/mcp-app.html ./
COPY packages/mcps/viewer-mcp/ui ./ui
RUN npm run build

# pdf-mcp UI -> /pdf/src/ra_mcp_pdf_mcp/dist
WORKDIR /pdf
COPY packages/mcps/pdf-mcp/package*.json ./
RUN npm ci
COPY packages/mcps/pdf-mcp/tsconfig.json packages/mcps/pdf-mcp/vite.config.ts packages/mcps/pdf-mcp/mcp-app.html ./
COPY packages/mcps/pdf-mcp/ui ./ui
RUN npm run build

# --- Stage 2: Build Python workspace with uv ---
FROM ${BUILDER_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1
WORKDIR /app

# Copy workspace configuration and all packages
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY src/ ./src/
COPY README.md LICENSE ./

# Copy BOTH built frontends into their packages before uv sync, so --no-editable includes
# each dist/mcp-app.html in the wheel (viewer AND pdf — the pdf one was previously missing).
COPY --from=frontend-builder /viewer/src/ra_mcp_viewer_mcp/dist/ ./packages/mcps/viewer-mcp/src/ra_mcp_viewer_mcp/dist/
COPY --from=frontend-builder /pdf/src/ra_mcp_pdf_mcp/dist/ ./packages/mcps/pdf-mcp/src/ra_mcp_pdf_mcp/dist/

# Sync workspace packages with diplomatics extra (--no-editable makes .venv self-contained)
RUN uv sync --frozen --no-cache --no-dev --no-editable --extra diplomatics


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

# Purge perl-base to clear several unfixed HIGH/CRITICAL CVEs (e.g. CVE-2026-42496,
# CVE-2026-8376). The runtime is pure Python (ra-serve) and never invokes perl; perl-base
# is marked Essential but has no installed reverse-deps in slim, so --allow-remove-essential
# removes it without cascade. This MUST run after the user-creation step above: on Debian
# addgroup/adduser are perl scripts, so purging perl first breaks them.
RUN if command -v apt-get >/dev/null 2>&1; then \
        apt-get purge -y --allow-remove-essential perl-base && \
        rm -rf /var/lib/apt/lists/*; \
    fi

WORKDIR /app

# Copy only what's needed at runtime (--chown avoids a separate chown layer)
# With --no-editable, .venv is self-contained — no need to copy src/ or packages/
COPY --from=builder --chown=ra-mcp:ra-mcp /app/.venv /app/.venv
COPY --from=builder --chown=ra-mcp:ra-mcp /app/src/ ./src/
COPY --from=builder --chown=ra-mcp:ra-mcp /app/packages/ ./packages/
COPY --chown=ra-mcp:ra-mcp docs/assets/ ./docs/assets/
COPY --chown=ra-mcp:ra-mcp packages/mcps/guide-mcp/resources/ ./resources/
COPY --chown=ra-mcp:ra-mcp plugins/ ./plugins/

RUN mkdir -p /app/data /data && chown ra-mcp:ra-mcp /app /app/data /data

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"
ENV GRADIO_SERVER_NAME="0.0.0.0"
# Datasets resolved via /data mount (hf-mount) or hf:// remote fallback
ENV RA_MCP_DATA_DIR="/data"

# Health check via /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:7860/health')" || exit 1

EXPOSE 7860
CMD ["ra-serve", "--http", "--host", "0.0.0.0", "--port", "7860"]
