# Build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY tsconfig.json vite.config.ts mcp-app.html ./
COPY ui ./ui
RUN npm run build

# Build Python dependencies
FROM python:3.13-alpine AS python-builder
WORKDIR /app
RUN apk add --no-cache gcc musl-dev libffi-dev
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
# Copy built frontend into package before uv sync
COPY --from=frontend-builder /app/src/ra_mcp_viewer_mcp/dist/ ./src/ra_mcp_viewer_mcp/dist/
RUN uv sync --frozen --no-cache --no-dev --no-editable

# Final runtime image
FROM python:3.13-alpine
WORKDIR /app
RUN apk add --no-cache ca-certificates libffi libgcc libstdc++
RUN addgroup -g 1000 mcp-app && adduser -u 1000 -G mcp-app -s /bin/sh -D mcp-app
COPY --from=python-builder --chown=mcp-app:mcp-app /app/.venv /app/.venv
RUN chown -R mcp-app:mcp-app /app
USER mcp-app
EXPOSE 3001
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys" || exit 1
CMD ["python", "-m", "ra_mcp_viewer_mcp.server"]
