"""Tests for Specialsök CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_specialsok_lib.ingest import (
    ingest_fangrullor,
    ingest_flygvapen,
    ingest_kurhuset,
    ingest_press,
    ingest_video,
)


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


# ---------------------------------------------------------------------------
# Flygvapenhaverier
# ---------------------------------------------------------------------------


def test_ingest_flygvapen(db):
    table = ingest_flygvapen(db, FIXTURES / "flygvapen_sample.csv")
    assert table.count_rows() == 5


def test_ingest_flygvapen_columns(db):
    table = ingest_flygvapen(db, FIXTURES / "flygvapen_sample.csv")
    schema_names = table.schema.names
    for col in ("datum", "fpl_typ", "havplats", "sammanfattning", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Fångrullor (no header CSV)
# ---------------------------------------------------------------------------


def test_ingest_fangrullor(db):
    table = ingest_fangrullor(db, FIXTURES / "fangrullor_sample.csv")
    assert table.count_rows() == 5


def test_ingest_fangrullor_columns(db):
    table = ingest_fangrullor(db, FIXTURES / "fangrullor_sample.csv")
    schema_names = table.schema.names
    for col in ("efternamn", "fornamn", "brott", "hemort", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Kurhuset
# ---------------------------------------------------------------------------


def test_ingest_kurhuset(db):
    table = ingest_kurhuset(db, FIXTURES / "kurhuset_sample.csv")
    assert table.count_rows() == 5


def test_ingest_kurhuset_columns(db):
    table = ingest_kurhuset(db, FIXTURES / "kurhuset_sample.csv")
    schema_names = table.schema.names
    for col in ("fornamn", "efternamn", "sjukdom", "hemort_socken", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Presskonferenser
# ---------------------------------------------------------------------------


def test_ingest_press(db):
    table = ingest_press(db, FIXTURES / "press_sample.csv")
    assert table.count_rows() == 5


def test_ingest_press_columns(db):
    table = ingest_press(db, FIXTURES / "press_sample.csv")
    schema_names = table.schema.names
    for col in ("titel", "innehaall", "aar", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Videobutiker
# ---------------------------------------------------------------------------


def test_ingest_video(db):
    table = ingest_video(db, FIXTURES / "video_sample.csv")
    assert table.count_rows() == 5


def test_ingest_video_columns(db):
    table = ingest_video(db, FIXTURES / "video_sample.csv")
    schema_names = table.schema.names
    for col in ("butiksnamn", "firmanamn", "kommun", "laen", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"
