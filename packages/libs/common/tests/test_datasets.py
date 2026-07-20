"""Tests for dataset path resolution."""

from pathlib import Path

from ra_mcp_common.datasets import (
    HF_OWNER,
    _resolve_project_root,
    resolve_dataset_path,
)
from ra_mcp_common.settings import settings


# ---------------------------------------------------------------------------
# _resolve_project_root
# ---------------------------------------------------------------------------


def test_resolve_project_root_finds_root():
    root = _resolve_project_root()
    assert root is not None
    assert (root / "pyproject.toml").exists()
    assert (root / "packages").exists()


# ---------------------------------------------------------------------------
# resolve_dataset_path — env var override
# ---------------------------------------------------------------------------


def test_resolve_dataset_path_env_override(monkeypatch):
    monkeypatch.setenv("TESTDB_LANCEDB_URI", "/custom/path/testdb")
    assert resolve_dataset_path("testdb") == "/custom/path/testdb"


def test_resolve_dataset_path_env_override_uppercase(monkeypatch):
    monkeypatch.setenv("MY_DATA_LANCEDB_URI", "s3://bucket/my_data")
    assert resolve_dataset_path("my_data") == "s3://bucket/my_data"


# ---------------------------------------------------------------------------
# resolve_dataset_path — local data/ directory
# ---------------------------------------------------------------------------


def test_resolve_dataset_path_local_data(monkeypatch, tmp_path):
    monkeypatch.delenv("DDS_LANCEDB_URI", raising=False)

    data_dir = tmp_path / "data" / "dds"
    data_dir.mkdir(parents=True)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")
    packages = tmp_path / "packages"
    packages.mkdir()

    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: tmp_path)

    result = resolve_dataset_path("dds")
    assert result == str(data_dir)


# ---------------------------------------------------------------------------
# resolve_dataset_path — mount point
# ---------------------------------------------------------------------------


def test_resolve_dataset_path_mount(monkeypatch, tmp_path):
    monkeypatch.delenv("MYDB_LANCEDB_URI", raising=False)
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)

    mount_dir = tmp_path / "mydb"
    mount_dir.mkdir()
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", tmp_path)

    result = resolve_dataset_path("mydb")
    assert result == str(mount_dir)


# ---------------------------------------------------------------------------
# resolve_dataset_path — HuggingFace fallback
# ---------------------------------------------------------------------------


def test_resolve_dataset_path_hf_fallback(monkeypatch):
    monkeypatch.delenv("NOEXIST_LANCEDB_URI", raising=False)
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)
    monkeypatch.setattr(
        "ra_mcp_common.datasets.MOUNT_DIR",
        type("P", (), {"__truediv__": lambda self, n: type("P", (), {"exists": lambda s: False})()})(),
    )

    result = resolve_dataset_path("noexist")
    assert result == f"hf://datasets/{HF_OWNER}/noexist-lance"


def test_resolve_dataset_path_hf_fallback_simple(monkeypatch, tmp_path):
    monkeypatch.delenv("XTEST_LANCEDB_URI", raising=False)
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", tmp_path / "nonexistent")

    result = resolve_dataset_path("xtest")
    assert result == f"hf://datasets/{HF_OWNER}/xtest-lance"


# ---------------------------------------------------------------------------
# Resolution priority
# ---------------------------------------------------------------------------


def test_env_var_takes_precedence_over_local(monkeypatch, tmp_path):
    monkeypatch.setenv("PRIO_LANCEDB_URI", "/env/override")

    data_dir = tmp_path / "data" / "prio"
    data_dir.mkdir(parents=True)
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: tmp_path)

    assert resolve_dataset_path("prio") == "/env/override"


def test_hf_owner_constant():
    assert HF_OWNER == "carpelan"


# ---------------------------------------------------------------------------
# resolve_dataset_path — boot-time staging: copy from mounted bucket to local disk
# ---------------------------------------------------------------------------


def _mount_dataset(mount: Path, name: str) -> Path:
    """Create a fake mounted dataset ``mount/<name>`` with one file, as if the bucket
    were mounted at ``mount``."""
    d = mount / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "table.lance").write_text("x")
    return d


def _copy_spy(record, real=True):
    """A stand-in for ``_copy_dataset`` that records (src, dst) and optionally does the
    real copy — so tests can assert whether a copy happened."""
    import shutil

    def _c(src, dst):
        record.append((str(src), str(dst)))
        if real:
            shutil.copytree(src, dst, dirs_exist_ok=True)

    return _c


def test_staging_copies_from_mount_and_returns_local(monkeypatch, tmp_path):
    """With staging enabled, the dataset is copied off the mount onto local disk and
    the local path is returned instead of the FUSE mount / hf:// remote."""
    monkeypatch.delenv("DDS_LANCEDB_URI", raising=False)
    mount, stage = tmp_path / "mount", tmp_path / "stage"
    _mount_dataset(mount, "dds")
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "")
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)
    monkeypatch.setattr("ra_mcp_common.datasets.STAGE_DIR", stage)

    result = resolve_dataset_path("dds")

    assert result == str(stage / "dds")
    assert (stage / "dds" / "table.lance").read_text() == "x"  # real copy landed


def test_staging_disabled_does_not_copy(monkeypatch, tmp_path):
    """When staging is off (the default), the dataset is read straight off the mount."""
    monkeypatch.delenv("MYDB_LANCEDB_URI", raising=False)
    mount = tmp_path / "mount"
    _mount_dataset(mount, "mydb")
    monkeypatch.setattr(settings, "stage_datasets", False)
    rec: list = []
    monkeypatch.setattr("ra_mcp_common.datasets._copy_dataset", _copy_spy(rec))
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)

    result = resolve_dataset_path("mydb")

    assert result == str(mount / "mydb")
    assert rec == []


def test_env_override_wins_over_staging(monkeypatch, tmp_path):
    """An explicit <NAME>_LANCEDB_URI short-circuits before any copy."""
    monkeypatch.setenv("PRIO_LANCEDB_URI", "/env/override")
    monkeypatch.setattr(settings, "stage_datasets", True)
    rec: list = []
    monkeypatch.setattr("ra_mcp_common.datasets._copy_dataset", _copy_spy(rec))

    assert resolve_dataset_path("prio") == "/env/override"
    assert rec == []


def test_staging_falls_back_when_not_on_mount(monkeypatch, tmp_path):
    """A dataset absent from the mount falls through to the remote fallback rather than
    breaking the dataset library import."""
    monkeypatch.delenv("GONE_LANCEDB_URI", raising=False)
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "")
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", tmp_path / "mount")  # empty
    monkeypatch.setattr("ra_mcp_common.datasets.STAGE_DIR", tmp_path / "stage")
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)

    result = resolve_dataset_path("gone")

    assert result == f"hf://datasets/{HF_OWNER}/gone-lance"


def test_staging_falls_back_to_mount_when_copy_fails(monkeypatch, tmp_path):
    """A failed copy is cleaned up and degrades to reading off the mount, not a crash."""
    monkeypatch.delenv("BROKEN_LANCEDB_URI", raising=False)
    mount, stage = tmp_path / "mount", tmp_path / "stage"
    _mount_dataset(mount, "broken")
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "")
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)
    monkeypatch.setattr("ra_mcp_common.datasets.STAGE_DIR", stage)
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)

    def _boom(src, dst):
        raise OSError("copy failed")

    monkeypatch.setattr("ra_mcp_common.datasets._copy_dataset", _boom)

    result = resolve_dataset_path("broken")

    assert result == str(mount / "broken")  # degrades to reading off the mount
    assert not (stage / "broken").exists()  # partial copy cleaned up


def test_staging_idempotent_returns_existing(monkeypatch, tmp_path):
    """An already-staged dataset (warm restart) is reused without re-copying."""
    monkeypatch.delenv("WARM_LANCEDB_URI", raising=False)
    mount, stage = tmp_path / "mount", tmp_path / "stage"
    _mount_dataset(mount, "warm")
    (stage / "warm").mkdir(parents=True)
    (stage / "warm" / "already.lance").write_text("y")
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "")
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)
    monkeypatch.setattr("ra_mcp_common.datasets.STAGE_DIR", stage)
    rec: list = []
    monkeypatch.setattr("ra_mcp_common.datasets._copy_dataset", _copy_spy(rec))

    result = resolve_dataset_path("warm")

    assert result == str(stage / "warm")
    assert rec == []  # already staged → no re-copy


def test_staging_respects_stage_only_allowlist(monkeypatch, tmp_path):
    """RA_MCP_STAGE_ONLY limits staging to named datasets; others aren't copied."""
    monkeypatch.delenv("OTHER_LANCEDB_URI", raising=False)
    mount = tmp_path / "mount"
    _mount_dataset(mount, "other")
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "dds,faltjagare")
    rec: list = []
    monkeypatch.setattr("ra_mcp_common.datasets._copy_dataset", _copy_spy(rec))
    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: None)
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)

    result = resolve_dataset_path("other")

    assert result == str(mount / "other")  # not staged → read off the mount
    assert rec == []


def test_staging_stages_allowlisted_dataset(monkeypatch, tmp_path):
    """A dataset named in RA_MCP_STAGE_ONLY is still copied to local disk."""
    monkeypatch.delenv("DDS_LANCEDB_URI", raising=False)
    mount, stage = tmp_path / "mount", tmp_path / "stage"
    _mount_dataset(mount, "dds")
    monkeypatch.setattr(settings, "stage_datasets", True)
    monkeypatch.setattr(settings, "stage_only", "dds,faltjagare")
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount)
    monkeypatch.setattr("ra_mcp_common.datasets.STAGE_DIR", stage)

    result = resolve_dataset_path("dds")

    assert result == str(stage / "dds")
    assert (stage / "dds" / "table.lance").exists()


def test_resolve_dataset_path_local_not_found_falls_to_mount(monkeypatch, tmp_path):
    """When local data dir doesn't exist, resolution falls through to mount."""
    monkeypatch.delenv("FALLTEST_LANCEDB_URI", raising=False)

    # Project root exists but data/falltest does NOT
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")
    packages = tmp_path / "packages"
    packages.mkdir()

    # Mount dir has the dataset
    mount_dir = tmp_path / "mounts"
    mount_dataset = mount_dir / "falltest"
    mount_dataset.mkdir(parents=True)

    monkeypatch.setattr("ra_mcp_common.datasets._resolve_project_root", lambda: tmp_path)
    monkeypatch.setattr("ra_mcp_common.datasets.MOUNT_DIR", mount_dir)

    result = resolve_dataset_path("falltest")
    assert result == str(mount_dataset)
