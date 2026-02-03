FROM python:3.12-alpine as builder

COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md LICENSE ./

RUN uv sync --frozen --no-cache

FROM python:3.12-alpine as production

# Create non-root user for security
RUN addgroup -g 1000 ra-mcp && \
    adduser -u 1000 -G ra-mcp -s /bin/sh -D ra-mcp

# Install only runtime dependencies
RUN apk add --no-cache ca-certificates libgcc libstdc++

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/LICENSE /app/pyproject.toml ./
COPY assets/index.html ./assets/index.html

RUN mkdir -p /app/data && chown -R ra-mcp:ra-mcp /app

RUN python -m pip install --no-cache-dir --upgrade pip==25.3

USER ra-mcp
ENV PATH="/app/.venv/bin:$PATH"
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Health check via Python import (lightweight)vilk
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys" || exit 1

EXPOSE 7860
CMD ["ra", "serve", "--host","0.0.0.0", "--port", "7860"]
