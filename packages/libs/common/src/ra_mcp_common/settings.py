"""Central typed runtime settings, sourced from RA_MCP_* environment variables.

A single validated settings object replaces scattered ``os.getenv`` reads for the
cross-cutting app config. Component-specific configuration — per-dataset
``<NAME>_LANCEDB_URI`` resolution, HTR / Label Studio credentials, dev-server
ports, and the CLI's runtime ``--log`` toggle — intentionally stays with its
component.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cross-cutting ra-mcp settings read once from the environment at import."""

    model_config = SettingsConfigDict(env_prefix="RA_MCP_", extra="ignore")

    log_level: str = "INFO"
    otel_enabled: bool = False
    data_dir: Path = Path("/data")
    # None = "no global override"; callers keep their own per-request timeout.
    timeout: int | None = None


settings = Settings()
