"""Tests for Aktiebolag search operations."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_aktiebolag_lib.ingest import ingest_aktiebolag
from ra_mcp_aktiebolag_lib.search_operations import AktiebolagSearch


FIXTURES = Path(__file__).parent / "fixtures"
BOLAG_FIXTURE = FIXTURES / "aktiebolag_sample.txt"
STYRELSE_FIXTURE = FIXTURES / "styrelsemedlemmar_sample.txt"


@pytest.fixture
def db(tmp_path):
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_aktiebolag(db, BOLAG_FIXTURE, STYRELSE_FIXTURE)
    return db


def test_search_bolag_basic(db):
    searcher = AktiebolagSearch(db)
    result = searcher.search_bolag("Separator")
    assert result.total_hits >= 1
    assert any("Separator" in r.get("bolagets_namn", "") for r in result.records)


def test_search_bolag_empty_keyword(db):
    searcher = AktiebolagSearch(db)
    with pytest.raises(ValueError, match="non-empty"):
        searcher.search_bolag("")


def test_search_bolag_filter_styrelsesate(db):
    searcher = AktiebolagSearch(db)
    result = searcher.search_bolag("AB", styrelsesate="Göteborg")
    for r in result.records:
        assert "göteborg" in r.get("styrelsesate", "").lower()


def test_search_styrelse_basic(db):
    searcher = AktiebolagSearch(db)
    result = searcher.search_styrelse("Wallenberg")
    assert result.total_hits >= 1
    assert any("Wallenberg" in r.get("styrelsemed", "") for r in result.records)


def test_search_styrelse_empty_keyword(db):
    searcher = AktiebolagSearch(db)
    with pytest.raises(ValueError, match="non-empty"):
        searcher.search_styrelse("")


def test_search_styrelse_filter_titel(db):
    searcher = AktiebolagSearch(db)
    result = searcher.search_styrelse("Wallenberg", titel="Bankir")
    for r in result.records:
        assert "bankir" in r.get("titel", "").lower()
