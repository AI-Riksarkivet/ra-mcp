# Multi-stage Python 3.12+ build for RA-MCP server
# Using Debian 13 (trixie) for latest security patches
FROM python:3.12-slim-trixie as builder

# Pin uv version for reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md LICENSE ./

RUN uv sync --frozen --no-cache

# Production stage - Debian 13 has fewer CVEs than Debian 12
FROM python:3.12-slim-trixie as production

# Create non-root user for security
RUN groupadd --gid 1000 ra-mcp && \
    useradd --uid 1000 --gid ra-mcp --shell /bin/bash --create-home ra-mcp

# Install only essential packages (ca-certificates for HTTPS)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/LICENSE /app/pyproject.toml ./
COPY assets/index.html ./assets/index.html

RUN mkdir -p /app/data && chown -R ra-mcp:ra-mcp /app

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Health check via Python import (lightweight)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys" || exit 1

EXPOSE 7860
CMD ["ra", "serve", "--host","0.0.0.0", "--port", "7860"]