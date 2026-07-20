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
    # Opt-in boot-time staging: copy each LanceDB dataset from the mounted bucket
    # (``data_dir``) onto local writable disk (``stage_dir``), then read it locally.
    # Needed on HuggingFace Spaces, whose /data bucket mount is a Xet FUSE layer that
    # fails Lance's concurrent random reads (os error 5) and atomic-rename commits (os
    # error 95). Off by default so dev/CI are unaffected.
    stage_datasets: bool = False
    stage_dir: Path = Path("/data-local")
    # Optional comma-separated allowlist of dataset names to stage (e.g. "dds,court").
    # Empty = stage every dataset. Lets a deployment that only enables some modules
    # avoid downloading all of them at boot.
    stage_only: str = ""
    # None = "no global override"; callers keep their own per-request timeout.
    timeout: int | None = None


settings = Settings()
