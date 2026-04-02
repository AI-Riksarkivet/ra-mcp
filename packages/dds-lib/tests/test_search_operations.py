"""Tests for DDSSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_dds_lib.ingest import ingest_doda, ingest_fodelse, ingest_vigsel
from ra_mcp_dds_lib.search_operations import DDSSearch


FIXTURES = Path(__file__).parent / "fixtures"
FODELSE_FIXTURE_DIR = FIXTURES / "fodda"
DODA_FIXTURE_DIR = FIXTURES / "doda"
VIGSEL_FIXTURE_DIR = FIXTURES / "vigslar"


@pytest.fixture
def search(tmp_path):
    """Return a DDSSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_fodelse(db, FODELSE_FIXTURE_DIR)
    ingest_doda(db, DODA_FIXTURE_DIR)
    ingest_vigsel(db, VIGSEL_FIXTURE_DIR)
    return DDSSearch(db)


# ---------------------------------------------------------------------------
# search_fodelse
# ---------------------------------------------------------------------------


def test_search_fodelse_returns_results(search):
    result = search.search_fodelse("Lindberg")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_fodelse_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_fodelse("")


def test_search_fodelse_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_fodelse("   ")


def test_search_fodelse_pagination(search):
    result = search.search_fodelse("Lindberg", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_fodelse_result_fields(search):
    result = search.search_fodelse("Lindberg")
    assert result.keyword == "Lindberg"
    assert result.offset == 0
    assert result.limit == 25


def test_search_fodelse_has_searchable_text(search):
    result = search.search_fodelse("Lindberg")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_fodelse_filter_lan(search):
    result = search.search_fodelse("Lindberg", lan="Stockholm")
    for rec in result.records:
        assert "stockholm" in rec.get("lan", "").lower()


def test_search_fodelse_filter_datum_from(search):
    result = search.search_fodelse("Lindberg", datum_from="1842-01-01")
    assert result.total_hits >= 1
    for rec in result.records:
        assert rec.get("datum", "") >= "1842-01-01"


def test_search_fodelse_filter_datum_till(search):
    result = search.search_fodelse("Lindberg", datum_till="1842-12-31")
    assert result.total_hits >= 1
    for rec in result.records:
        assert rec.get("datum", "") <= "1842-12-31"


def test_search_fodelse_filter_datum_range(search):
    result = search.search_fodelse("Lindberg", datum_from="1842-01-01", datum_till="1842-12-31")
    assert result.total_hits >= 1
    for rec in result.records:
        assert "1842-01-01" <= rec.get("datum", "") <= "1842-12-31"


def test_search_fodelse_filter_datum_range_no_results(search):
    result = search.search_fodelse("Lindberg", datum_from="1900-01-01", datum_till="1900-12-31")
    assert result.total_hits == 0


# ---------------------------------------------------------------------------
# search_doda
# ---------------------------------------------------------------------------


def test_search_doda_returns_results(search):
    result = search.search_doda("Lindberg")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_doda_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_doda("")


def test_search_doda_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_doda("   ")


def test_search_doda_pagination(search):
    result = search.search_doda("Lindberg", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_doda_result_fields(search):
    result = search.search_doda("Lindberg")
    assert result.keyword == "Lindberg"
    assert result.offset == 0
    assert result.limit == 25


def test_search_doda_has_searchable_text(search):
    result = search.search_doda("Lindberg")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_doda_filter_dodsorsak(search):
    result = search.search_doda("Lindberg", dodsorsak="Tuberkulos")
    for rec in result.records:
        has_match = "tuberkulos" in rec.get("dodsorsak", "").lower() or "tuberkulos" in rec.get("dodsorsak_klassificerat", "").lower()
        assert has_match


def test_search_doda_filter_datum_from(search):
    result = search.search_doda("Lindberg", datum_from="1856-01-01")
    for rec in result.records:
        assert rec.get("datum", "") >= "1856-01-01"


def test_search_doda_filter_datum_till(search):
    result = search.search_doda("Lindberg", datum_till="1855-06-01")
    assert result.total_hits >= 1
    for rec in result.records:
        assert rec.get("datum", "") <= "1855-06-01"


def test_search_doda_filter_datum_range(search):
    result = search.search_doda("Lindberg", datum_from="1855-01-01", datum_till="1855-12-31")
    assert result.total_hits >= 1
    for rec in result.records:
        assert "1855-01-01" <= rec.get("datum", "") <= "1855-12-31"


# ---------------------------------------------------------------------------
# search_vigsel
# ---------------------------------------------------------------------------


def test_search_vigsel_returns_results(search):
    result = search.search_vigsel("Lindberg")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_vigsel_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_vigsel("")


def test_search_vigsel_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_vigsel("   ")


def test_search_vigsel_pagination(search):
    result = search.search_vigsel("Lindberg", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_vigsel_result_fields(search):
    result = search.search_vigsel("Lindberg")
    assert result.keyword == "Lindberg"
    assert result.offset == 0
    assert result.limit == 25


def test_search_vigsel_has_searchable_text(search):
    result = search.search_vigsel("Lindberg")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_vigsel_filter_lan(search):
    result = search.search_vigsel("Lindberg", lan="Stockholm")
    for rec in result.records:
        assert "stockholm" in rec.get("lan", "").lower()


def test_search_vigsel_filter_datum_from(search):
    result = search.search_vigsel("Lindberg", datum_from="1851-01-01")
    for rec in result.records:
        assert rec.get("datum", "") >= "1851-01-01"


def test_search_vigsel_filter_datum_till(search):
    result = search.search_vigsel("Lindberg", datum_till="1850-12-31")
    assert result.total_hits >= 1
    for rec in result.records:
        assert rec.get("datum", "") <= "1850-12-31"


def test_search_vigsel_filter_datum_range(search):
    result = search.search_vigsel("Lindberg", datum_from="1850-01-01", datum_till="1850-12-31")
    assert result.total_hits >= 1
    for rec in result.records:
        assert "1850-01-01" <= rec.get("datum", "") <= "1850-12-31"
