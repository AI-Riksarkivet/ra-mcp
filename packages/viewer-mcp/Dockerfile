# Build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY tsconfig.json vite.config.ts mcp-app.html ./
COPY ui ./ui
RUN npm run build

# Build Python dependencies
FROM python:3.12-alpine AS python-builder
WORKDIR /app
RUN apk add --no-cache gcc musl-dev libffi-dev
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

# Final runtime image
FROM python:3.12-alpine
WORKDIR /app
RUN apk add --no-cache ca-certificates libffi libgcc libstdc++
RUN addgroup -g 1000 mcp-app && adduser -u 1000 -G mcp-app -s /bin/sh -D mcp-app
COPY --from=python-builder --chown=mcp-app:mcp-app /app/.venv /app/.venv
COPY --from=frontend-builder --chown=mcp-app:mcp-app /app/dist /app/dist
COPY --chown=mcp-app:mcp-app server.py ./
COPY --chown=mcp-app:mcp-app src/ ./src/
RUN chown -R mcp-app:mcp-app /app
USER mcp-app
EXPOSE 3001
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys" || exit 1
CMD ["python", "server.py"]
