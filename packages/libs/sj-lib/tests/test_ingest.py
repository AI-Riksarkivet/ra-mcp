"""Tests for SJ railway records CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sj_lib.ingest import ingest_juda, ingest_ritningar


FIXTURES = Path(__file__).parent / "fixtures"
JUDA_FIXTURE_DIR = FIXTURES  # JDA*.csv pattern won't match; we use juda_sample.csv
FIRA_FIXTURE = FIXTURES / "fira_sample.csv"
SIRA_FIXTURE_DIR = FIXTURES  # contains sira_sample.csv
DKOD_FIXTURE = FIXTURES / "dkod_sample.csv"
SAKG_FIXTURE = FIXTURES / "sakg_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


@pytest.fixture
def juda_dir(tmp_path):
    """Create a temp directory with JDA-named CSV files for ingest_juda."""
    juda_dir = tmp_path / "juda"
    juda_dir.mkdir()
    # Copy fixture as JDA90.csv
    src = FIXTURES / "juda_sample.csv"
    dst = juda_dir / "JDA90.csv"
    dst.write_bytes(src.read_bytes())
    return juda_dir


# ---------------------------------------------------------------------------
# JUDA ingest
# ---------------------------------------------------------------------------


def test_ingest_juda(db, juda_dir):
    table = ingest_juda(db, juda_dir)
    assert table.count_rows() == 5


def test_ingest_juda_columns(db, juda_dir):
    table = ingest_juda(db, juda_dir)
    schema_names = table.schema.names
    for col in ("fbidnr", "fbtext", "fblan", "fbkom", "fbagrkod2", "fbanm", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_juda_no_files_raises(db, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        ingest_juda(db, empty_dir)


# ---------------------------------------------------------------------------
# Ritningar ingest (FIRA + SIRA)
# ---------------------------------------------------------------------------


@pytest.fixture
def sira_dir(tmp_path):
    """Create a temp directory with SIRA-named CSV files for ingest."""
    sira_dir = tmp_path / "sira"
    sira_dir.mkdir()
    src = FIXTURES / "sira_sample.csv"
    dst = sira_dir / "SIRA_1.csv"
    dst.write_bytes(src.read_bytes())
    return sira_dir


def test_ingest_ritningar(db, sira_dir):
    table = ingest_ritningar(db, FIRA_FIXTURE, sira_dir)
    assert table.count_rows() == 10  # 5 FIRA + 5 SIRA


def test_ingest_ritningar_columns(db, sira_dir):
    table = ingest_ritningar(db, FIRA_FIXTURE, sira_dir)
    schema_names = table.schema.names
    for col in ("bnum", "blad", "ben1", "ben", "ritn", "datm", "dkod", "sakg", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_ritningar_with_lookups(db, sira_dir):
    table = ingest_ritningar(db, FIRA_FIXTURE, sira_dir, dkod_path=DKOD_FIXTURE, sakg_path=SAKG_FIXTURE)
    # Search for HUS which appears in FIRA fixture and check enriched DKOD/SAKG
    rows = table.search("HUS", query_type="fts").limit(10).to_list()
    assert len(rows) >= 1
    # At least one row should have enriched dkod containing the lookup description
    enriched = [r for r in rows if "distrikt" in r.get("dkod", "").lower()]
    assert len(enriched) >= 1


def test_ingest_ritningar_fira_only(db, tmp_path):
    empty_sira = tmp_path / "empty_sira"
    empty_sira.mkdir()
    table = ingest_ritningar(db, FIRA_FIXTURE, empty_sira)
    assert table.count_rows() == 5  # FIRA only
