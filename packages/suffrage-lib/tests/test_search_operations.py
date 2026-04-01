"""Tests for SuffrageSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_suffrage_lib.ingest import ingest_fkpr, ingest_rostratt
from ra_mcp_suffrage_lib.search_operations import SuffrageSearch


FIXTURES = Path(__file__).parent / "fixtures"
ROSTRATT_FIXTURE_DIR = FIXTURES / "rostratt"
FKPR_FIXTURE = FIXTURES / "fkpr_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a SuffrageSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_rostratt(db, ROSTRATT_FIXTURE_DIR)
    ingest_fkpr(db, FKPR_FIXTURE)
    return SuffrageSearch(db)


# ---------------------------------------------------------------------------
# search_rostratt
# ---------------------------------------------------------------------------


def test_search_rostratt_returns_results(search):
    result = search.search_rostratt("Svensson")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_rostratt_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_rostratt("")


def test_search_rostratt_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_rostratt("   ")


def test_search_rostratt_pagination(search):
    result = search.search_rostratt("Svensson", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_rostratt_result_fields(search):
    result = search.search_rostratt("Svensson")
    assert result.keyword == "Svensson"
    assert result.offset == 0
    assert result.limit == 25


def test_search_rostratt_has_searchable_text(search):
    result = search.search_rostratt("Svensson")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_rostratt_filter_lan(search):
    result = search.search_rostratt("Svensson", lan="Blekinge")
    for rec in result.records:
        assert "blekinge" in rec.get("lan", "").lower()


# ---------------------------------------------------------------------------
# search_fkpr
# ---------------------------------------------------------------------------


def test_search_fkpr_returns_results(search):
    result = search.search_fkpr("Lindberg")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_fkpr_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_fkpr("")


def test_search_fkpr_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_fkpr("   ")


def test_search_fkpr_pagination(search):
    result = search.search_fkpr("Lindberg", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_fkpr_result_fields(search):
    result = search.search_fkpr("Lindberg")
    assert result.keyword == "Lindberg"
    assert result.offset == 0
    assert result.limit == 25


def test_search_fkpr_has_searchable_text(search):
    result = search.search_fkpr("Lindberg")
    assert result.records
    assert "searchable_text" in result.records[0]
