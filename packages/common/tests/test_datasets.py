"""Tests for dataset path resolution."""

import pytest

from ra_mcp_common.datasets import (
    HF_OWNER,
    _resolve_project_root,
    resolve_dataset_path,
)


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

    monkeypatch.setattr(
        "ra_mcp_common.datasets._resolve_project_root", lambda: tmp_path
    )

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
        type("P", (), {"__truediv__": lambda self, n: type("P", (), {"exists": lambda s: False})()} )(),
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
    monkeypatch.setattr(
        "ra_mcp_common.datasets._resolve_project_root", lambda: tmp_path
    )

    assert resolve_dataset_path("prio") == "/env/override"


def test_hf_owner_constant():
    assert HF_OWNER == "carpelan"


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
