"""Tests for FilmcensurSearch over ingested Filmreg sample data."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_filmcensur_lib.ingest import ingest_filmreg
from ra_mcp_filmcensur_lib.search_operations import FilmcensurSearch


FIXTURES = Path(__file__).parent / "fixtures"
FILMREG_FIXTURE = FIXTURES / "filmreg_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a FilmcensurSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_filmreg(db, FILMREG_FIXTURE)
    return FilmcensurSearch(db)


def test_search_returns_results(search):
    result = search.search_filmreg("Spelfilm")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_filmreg("")


def test_search_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_filmreg("   ")


def test_search_pagination(search):
    result = search.search_filmreg("Spelfilm", limit=2)
    assert len(result.records) <= 2
    assert result.limit == 2


def test_search_result_fields(search):
    result = search.search_filmreg("Spelfilm")
    assert result.keyword == "Spelfilm"
    assert result.offset == 0
    assert result.limit == 25


def test_search_has_searchable_text(search):
    result = search.search_filmreg("Spelfilm")
    assert result.records
    assert "searchable_text" in result.records[0]
