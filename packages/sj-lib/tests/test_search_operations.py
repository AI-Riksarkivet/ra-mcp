"""Tests for SJSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sj_lib.ingest import ingest_juda, ingest_ritningar
from ra_mcp_sj_lib.search_operations import SJSearch


FIXTURES = Path(__file__).parent / "fixtures"
FIRA_FIXTURE = FIXTURES / "fira_sample.csv"


@pytest.fixture
def juda_dir(tmp_path):
    juda_dir = tmp_path / "juda"
    juda_dir.mkdir()
    src = FIXTURES / "juda_sample.csv"
    dst = juda_dir / "JDA90.csv"
    dst.write_bytes(src.read_bytes())
    return juda_dir


@pytest.fixture
def sira_dir(tmp_path):
    sira_dir = tmp_path / "sira"
    sira_dir.mkdir()
    src = FIXTURES / "sira_sample.csv"
    dst = sira_dir / "SIRA_1.csv"
    dst.write_bytes(src.read_bytes())
    return sira_dir


@pytest.fixture
def search(tmp_path, juda_dir, sira_dir):
    """Return an SJSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_juda(db, juda_dir)
    ingest_ritningar(db, FIRA_FIXTURE, sira_dir)
    return SJSearch(db)


# ---------------------------------------------------------------------------
# search_juda
# ---------------------------------------------------------------------------


def test_search_juda_returns_results(search):
    result = search.search_juda("Jernhusen")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_juda_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_juda("")


def test_search_juda_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_juda("   ")


def test_search_juda_pagination(search):
    result = search.search_juda("Jernhusen", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_juda_result_fields(search):
    result = search.search_juda("Jernhusen")
    assert result.keyword == "Jernhusen"
    assert result.offset == 0
    assert result.limit == 25


def test_search_juda_has_searchable_text(search):
    result = search.search_juda("Jernhusen")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_juda_filter_fbagrkod2(search):
    result = search.search_juda("Stationshus", fbagrkod2="Jernhusen")
    for rec in result.records:
        assert "jernhusen" in rec.get("fbagrkod2", "").lower()


# ---------------------------------------------------------------------------
# search_ritningar
# ---------------------------------------------------------------------------


def test_search_ritningar_returns_results(search):
    result = search.search_ritningar("STATION")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_ritningar_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_ritningar("")


def test_search_ritningar_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_ritningar("   ")


def test_search_ritningar_pagination(search):
    result = search.search_ritningar("STATION", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_ritningar_result_fields(search):
    result = search.search_ritningar("STATION")
    assert result.keyword == "STATION"
    assert result.offset == 0
    assert result.limit == 25


def test_search_ritningar_has_searchable_text(search):
    result = search.search_ritningar("STATION")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_ritningar_filter_dkod(search):
    result = search.search_ritningar("GÖTEBORG", dkod="GBG")
    for rec in result.records:
        assert "gbg" in rec.get("dkod", "").lower()
