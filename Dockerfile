# Multi-stage Python 3.12+ build for RA-MCP server
FROM python:3.12-slim as builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Copy source code needed for package installation
COPY src/ ./src/
COPY README.md LICENSE ./

# Create virtual environment and install dependencies + package
RUN uv sync --frozen --no-cache

# Production stage
FROM python:3.12-slim as production

# Create non-root user for security
RUN groupadd --gid 1000 ra-mcp && \
    useradd --uid 1000 --gid ra-mcp --shell /bin/bash --create-home ra-mcp

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy installed package and source
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/LICENSE ./

# Copy static assets (index.html) to assets directory
COPY assets/index.html ./assets/index.html

# Create directory for potential data/cache and set ownership
RUN mkdir -p /app/data && chown -R ra-mcp:ra-mcp /app

# Switch to non-root user
USER ra-mcp

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.ra_mcp.server; print('Server module loads successfully')" || exit 1

# Default to running the MCP server with HTTP transport
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD ["ra", "serve", "--host","0.0.0.0", "--port", "7860"]