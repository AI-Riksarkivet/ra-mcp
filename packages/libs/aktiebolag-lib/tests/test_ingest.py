"""Tests for Aktiebolag CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_aktiebolag_lib.ingest import ingest_aktiebolag


FIXTURES = Path(__file__).parent / "fixtures"
BOLAG_FIXTURE = FIXTURES / "aktiebolag_sample.txt"
STYRELSE_FIXTURE = FIXTURES / "styrelsemedlemmar_sample.txt"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_aktiebolag_row_counts(db):
    bolag_table, styrelse_table = ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    assert bolag_table.count_rows() == 5
    assert styrelse_table.count_rows() == 5


def test_ingest_bolag_columns(db):
    bolag_table, _ = ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    schema_names = bolag_table.schema.names
    for col in ("post_id", "bolagets_namn", "styrelsesate", "bolagets_andamal", "styrelsemedlemmar", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_styrelse_columns(db):
    _, styrelse_table = ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    schema_names = styrelse_table.schema.names
    for col in ("id", "post_id", "styrelsemed", "fornamn", "titel", "bolagets_namn", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_bolag_join(db):
    bolag_table, _ = ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    rows = bolag_table.to_arrow().to_pylist()
    row_1 = next(r for r in rows if r["post_id"] == 1)
    assert "Bernstr" in row_1["styrelsemedlemmar"]
    assert "De Laval" in row_1["styrelsemedlemmar"]


def test_ingest_styrelse_join(db):
    _, styrelse_table = ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    rows = styrelse_table.to_arrow().to_pylist()
    row_1 = next(r for r in rows if r["id"] == 1)
    assert row_1["bolagets_namn"] == "AB Separator"
