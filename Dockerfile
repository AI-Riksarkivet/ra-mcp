FROM python:3.12-alpine as builder

COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/
WORKDIR /app

# Copy workspace configuration and all packages
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY README.md LICENSE ./

# Sync workspace packages
RUN uv sync --frozen --no-cache --no-dev

FROM python:3.12-alpine as production

# Upgrade all packages to fix CVEs (including busybox CVE-2025-60877)
RUN apk upgrade --no-cache

# Install minimal runtime dependencies (ca-certificates for HTTPS, libgcc for cryptography)
RUN apk add --no-cache ca-certificates libgcc

# Remove pip and setuptools to eliminate CVE-2025-8869 and CVE-2026-1703
# We use uv for all package management, so pip is not needed at runtime
RUN pip uninstall -y pip setuptools wheel || true && \
    rm -rf /usr/local/lib/python3.12/site-packages/pip* \
           /usr/local/lib/python3.12/site-packages/setuptools* \
           /usr/local/lib/python3.12/site-packages/wheel* \
           /usr/local/bin/pip* 2>/dev/null || true

# Create non-root user for security
RUN addgroup -g 1000 ra-mcp && \
    adduser -u 1000 -G ra-mcp -s /bin/sh -D ra-mcp

WORKDIR /app

# Copy only what's needed at runtime
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/packages /app/packages
COPY assets/index.html ./assets/index.html
COPY resources/ ./resources/

RUN mkdir -p /app/data && chown -R ra-mcp:ra-mcp /app

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Health check via Python import (lightweight)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys" || exit 1

EXPOSE 7860
CMD ["ra", "serve", "--host", "0.0.0.0", "--port", "7860"]
