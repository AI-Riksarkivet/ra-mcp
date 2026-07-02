"""Tests for WincarsSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_wincars_lib.ingest import ingest_wincars
from ra_mcp_wincars_lib.search_operations import WincarsSearch


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def search(tmp_path):
    """Return a WincarsSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_wincars(db, FIXTURES)
    return WincarsSearch(db)


def test_search_returns_results(search):
    result = search.search("Volvo")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("")


def test_search_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("   ")


def test_search_pagination(search):
    result = search.search("Volvo", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_result_fields(search):
    result = search.search("Volvo")
    assert result.keyword == "Volvo"
    assert result.offset == 0
    assert result.limit == 25


def test_search_has_searchable_text(search):
    result = search.search("Volvo")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_filter_typ(search):
    result = search.search("Volvo", typ="PB")
    for rec in result.records:
        assert "pb" in rec.get("typ", "").lower()


def test_search_filter_hemvist(search):
    result = search.search("Volvo", hemvist="Sundsvall")
    for rec in result.records:
        assert "sundsvall" in rec.get("hemvist", "").lower()


def test_search_filter_fabrikat(search):
    result = search.search("Sundsvall", fabrikat="Volvo")
    for rec in result.records:
        assert "volvo" in rec.get("fabrikat", "").lower()
