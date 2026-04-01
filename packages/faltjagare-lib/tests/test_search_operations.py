"""Tests for FaltjagareSearch over ingested sample data."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_faltjagare_lib.ingest import ingest_faltjagare
from ra_mcp_faltjagare_lib.search_operations import FaltjagareSearch


FIXTURES = Path(__file__).parent / "fixtures"
FALTJAGARE_FIXTURE = FIXTURES / "faltjagare_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a FaltjagareSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_faltjagare(db, FALTJAGARE_FIXTURE)
    return FaltjagareSearch(db)


def test_search_returns_results(search):
    result = search.search("Soldat")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("")


def test_search_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("   ")


def test_search_pagination(search):
    result = search.search("Soldat", limit=2)
    assert len(result.records) <= 2
    assert result.limit == 2


def test_search_result_fields(search):
    result = search.search("Soldat")
    assert result.keyword == "Soldat"
    assert result.offset == 0
    assert result.limit == 25


def test_search_has_searchable_text(search):
    result = search.search("Soldat")
    assert result.records
    assert "searchable_text" in result.records[0]
