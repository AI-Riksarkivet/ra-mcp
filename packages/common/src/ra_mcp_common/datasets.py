"""Resolve LanceDB dataset paths — local first, HuggingFace remote fallback.

When a local data/ path doesn't exist, returns an hf:// URI so LanceDB
reads directly from HuggingFace without downloading.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("ra_mcp.datasets")

# HuggingFace org/user for dataset repos
HF_OWNER = "carpelan"


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
    2. Local data/<name>/ relative to project root
    3. HuggingFace remote via hf://datasets/carpelan/<name>-lance

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

    # 2. Check local data/ directory
    root = _resolve_project_root()
    if root:
        local_path = root / "data" / name
        if local_path.exists():
            return str(local_path)

    # 3. HuggingFace remote — LanceDB reads directly via hf:// protocol
    hf_uri = f"hf://datasets/{HF_OWNER}/{name}-lance"
    logger.info("Using remote dataset: %s", hf_uri)
    return hf_uri
