# Multi-stage Python 3.12+ build for RA-MCP server
FROM python:3.12-slim as builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md LICENSE ./

RUN uv sync --frozen --no-cache

# Production stage
FROM python:3.12-slim as production

# Create non-root user for security
RUN groupadd --gid 1000 ra-mcp && \
    useradd --uid 1000 --gid ra-mcp --shell /bin/bash --create-home ra-mcp

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/LICENSE /app/pyproject.toml ./
COPY assets/index.html ./assets/index.html

RUN mkdir -p /app/data && chown -R ra-mcp:ra-mcp /app

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.ra_mcp.server; print('Server module loads successfully')" || exit 1

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD ["ra", "serve", "--host","0.0.0.0", "--port", "7860"]