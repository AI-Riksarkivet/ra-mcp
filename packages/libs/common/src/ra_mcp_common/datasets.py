"""Resolve LanceDB dataset paths — env override, local stage, mount, or HF remote.

Resolution order:
1. Environment variable <NAME>_LANCEDB_URI
2. Boot-time staging to local disk (when ``RA_MCP_STAGE_DATASETS`` is set): copy the
   dataset from the mounted bucket (``data_dir/<name>``) onto the writable ``stage_dir``
   once, then read it from local disk.
3. Local data/<name>/ relative to project root (development)
4. /data/<name>/ mount point (the mounted bucket)
5. hf://datasets/carpelan/<name>-lance (remote fallback)

Staging exists for HuggingFace Spaces. There the ``Riksarkivet/lance`` storage bucket is
mounted at /data through a Xet-backed FUSE layer, and Lance's concurrent random-access
reads fail on it (``os error 5`` EIO) while its atomic-rename commit path is unsupported
(``os error 95``) — regardless of the mount being read-write. Copying each dataset from
the mount onto the Space's ordinary ephemeral disk once at boot moves every query onto a
real POSIX filesystem, which removes both errors. The mount stays the source of truth; we
just stop serving queries directly off the FUSE layer.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from time import perf_counter

from ra_mcp_common.settings import settings


logger = logging.getLogger("ra_mcp.datasets")

# HuggingFace org/user for the dataset repos used only as the last-resort remote fallback.
HF_OWNER = "carpelan"

# Mount point for the Riksarkivet/lance bucket (the authoritative source).
MOUNT_DIR = settings.data_dir

# Writable local target for boot-time staging (ephemeral disk on HF Spaces).
STAGE_DIR = settings.stage_dir


def _resolve_project_root() -> Path | None:
    """Walk up from this file to find the project root (has pyproject.toml + packages/)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists() and (current / "packages").exists():
            return current
        current = current.parent
    return None


def _is_populated(path: Path) -> bool:
    """True if ``path`` is a directory containing at least one entry."""
    return path.is_dir() and any(path.iterdir())


def _copy_dataset(src: Path, dst: Path) -> None:
    """Copy a dataset directory from the mounted bucket to local disk.

    Split out so tests can substitute it. ``dirs_exist_ok`` lets a previous partial copy
    be overwritten; on failure the caller removes ``dst`` so a truncated dataset is never
    served.
    """
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _should_stage(name: str) -> bool:
    """Whether ``name`` is in the staging allowlist (empty allowlist = stage all)."""
    only = settings.stage_only.strip()
    if not only:
        return True
    allow = {s.strip() for s in only.split(",") if s.strip()}
    return name in allow


def _stage_from_mount(name: str) -> Path | None:
    """Copy ``name`` from the mounted bucket to local disk; return its local path.

    Returns ``None`` to fall through to normal resolution when the dataset is not on the
    mount, or when the copy fails — a single unavailable dataset must not break startup.
    A copy that is interrupted is cleaned up so we never serve a half-copied dataset. Only
    a bulk sequential read of the mount happens here (at boot), not the concurrent random
    reads that trip ``os error 5`` at query time.
    """
    src = MOUNT_DIR / name
    dst = STAGE_DIR / name

    if _is_populated(dst):
        logger.info("Dataset '%s' already staged at %s", name, dst)
        return dst

    if not _is_populated(src):
        logger.info("Dataset '%s' not present on mount %s — skipping local staging", name, src)
        return None

    try:
        logger.info("Staging dataset '%s' from mount %s → %s ...", name, src, dst)
        start = perf_counter()
        _copy_dataset(src, dst)
        logger.info("Staged dataset '%s' in %.1fs", name, perf_counter() - start)
    except Exception as e:
        logger.error("Failed to stage dataset '%s' from mount: %s — falling back", name, e)
        shutil.rmtree(dst, ignore_errors=True)
        return None

    return dst


def resolve_dataset_path(name: str) -> str:
    """Resolve the path to a LanceDB dataset by name.

    Resolution order:
    1. Environment variable <NAME>_LANCEDB_URI (e.g. DDS_LANCEDB_URI)
    2. Boot-time staging: copy from the mounted bucket to local disk (RA_MCP_STAGE_DATASETS)
    3. Local data/<name>/ relative to project root (development)
    4. /data/<name>/ mount point (the mounted bucket)
    5. hf://datasets/carpelan/<name>-lance (remote fallback)

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

    # 2. Stage from the mounted bucket onto local disk (opt-in) — see module docstring for
    #    why this is required on HF Spaces. Falls through when the dataset is not mounted.
    if settings.stage_datasets and _should_stage(name):
        staged = _stage_from_mount(name)
        if staged is not None:
            return str(staged)

    # 3. Check local data/ directory (development)
    root = _resolve_project_root()
    if root:
        local_path = root / "data" / name
        if local_path.exists():
            return str(local_path)

    # 4. Check mount point (the mounted bucket)
    mount_path = MOUNT_DIR / name
    if mount_path.exists():
        logger.info("Using mounted dataset: %s", mount_path)
        return str(mount_path)

    # 5. HuggingFace remote — LanceDB reads directly via hf:// protocol
    hf_uri = f"hf://datasets/{HF_OWNER}/{name}-lance"
    logger.info("Using remote dataset: %s", hf_uri)
    return hf_uri
