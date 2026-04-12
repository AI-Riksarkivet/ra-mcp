"""Resolve LanceDB dataset paths — local first, HuggingFace fallback.

When a local data/ path doesn't exist, downloads the dataset from
HuggingFace (carpelan/<name>-lance) into a cache directory.

Requires huggingface_hub to be installed for the download fallback.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("ra_mcp.datasets")

# HuggingFace org/user for dataset repos
HF_OWNER = "carpelan"

# Cache directory for downloaded datasets
_CACHE_DIR = Path(os.getenv("RA_MCP_DATA_CACHE", Path.home() / ".cache" / "ra-mcp" / "data"))


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
    3. Download from HuggingFace carpelan/<name>-lance to cache

    Args:
        name: Dataset name (e.g. "dds", "rosenberg", "aktiebolag").

    Returns:
        Absolute path to the LanceDB directory.
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

    # 3. Check cache
    cache_path = _CACHE_DIR / name
    if cache_path.exists():
        return str(cache_path)

    # 4. Download from HuggingFace
    repo_id = f"{HF_OWNER}/{name}-lance"
    logger.info("Downloading dataset %s from HuggingFace to %s ...", repo_id, cache_path)

    try:
        from huggingface_hub import snapshot_download

        downloaded = snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(cache_path),
        )
        logger.info("Downloaded %s to %s", repo_id, downloaded)
        return str(cache_path)

    except ImportError:
        logger.error(
            "huggingface_hub not installed. Install it with: pip install huggingface_hub\n"
            "Or set %s to a local path, or place data in data/%s/",
            env_key,
            name,
        )
        raise
    except Exception as e:
        logger.error("Failed to download %s: %s", repo_id, e)
        raise
