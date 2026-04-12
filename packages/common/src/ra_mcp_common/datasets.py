"""Resolve LanceDB dataset paths — local, mount, or HuggingFace remote fallback.

Resolution order:
1. Environment variable <NAME>_LANCEDB_URI
2. Local data/<name>/ relative to project root (development)
3. /data/<name>/ mount point (Docker with hf-mount)
4. hf://datasets/carpelan/<name>-lance (remote fallback)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("ra_mcp.datasets")

# HuggingFace org/user for dataset repos (remote fallback)
HF_OWNER = "carpelan"

# Mount point for hf-mount in Docker
MOUNT_DIR = Path(os.getenv("RA_MCP_DATA_DIR", "/data"))


def _resolve_project_root() -> Path | None:
    """Walk up from this file to find the project root (has pyproject.toml + packages/)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists() and (current / "packages").exists():
            return current
        current = current.parent
    return None


def resolve_dataset_path(name: str) -> str:
    """Resolve the path to a LanceDB dataset by name.

    Resolution order:
    1. Environment variable <NAME>_LANCEDB_URI (e.g. DDS_LANCEDB_URI)
    2. Local data/<name>/ relative to project root (development)
    3. /data/<name>/ mount point (Docker with hf-mount)
    4. hf://datasets/carpelan/<name>-lance (remote fallback)

    Args:
        name: Dataset name (e.g. "dds", "rosenberg", "aktiebolag").

    Returns:
        Local path or hf:// URI for LanceDB.connect().
    """
    # 1. Check env var override
    env_key = f"{name.upper()}_LANCEDB_URI"
    env_val = os.getenv(env_key)
    if env_val:
        return env_val

    # 2. Check local data/ directory (development)
    root = _resolve_project_root()
    if root:
        local_path = root / "data" / name
        if local_path.exists():
            return str(local_path)

    # 3. Check mount point (Docker with hf-mount)
    mount_path = MOUNT_DIR / name
    if mount_path.exists():
        logger.info("Using mounted dataset: %s", mount_path)
        return str(mount_path)

    # 4. HuggingFace remote — LanceDB reads directly via hf:// protocol
    hf_uri = f"hf://datasets/{HF_OWNER}/{name}-lance"
    logger.info("Using remote dataset: %s", hf_uri)
    return hf_uri
