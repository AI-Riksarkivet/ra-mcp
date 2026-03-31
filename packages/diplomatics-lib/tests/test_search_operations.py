"""Tests for DiplomaticsSearch over ingested SDHK and MPO sample data."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_diplomatics_lib.ingest import ingest_mpo, ingest_sdhk
from ra_mcp_diplomatics_lib.search_operations import DiplomaticsSearch

FIXTURES = Path(__file__).parent / "fixtures"
SDHK_FIXTURE = FIXTURES / "sdhk_sample.csv"
MPO_FIXTURE = FIXTURES / "mpo_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a DiplomaticsSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_sdhk(db, SDHK_FIXTURE)
    ingest_mpo(db, MPO_FIXTURE)
    return DiplomaticsSearch(db)


def test_search_sdhk_returns_results(search):
    result = search.search_sdhk("Kung")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_sdhk_empty_keyword_returns_error(search):
    with pytest.raises(ValueError):
        search.search_sdhk("")


def test_search_sdhk_whitespace_keyword_returns_error(search):
    with pytest.raises(ValueError):
        search.search_sdhk("   ")


def test_search_sdhk_pagination(search):
    result = search.search_sdhk("Kung", limit=2)
    assert len(result.records) <= 2
    assert result.limit == 2


def test_search_mpo_returns_results(search):
    result = search.search_mpo("Missale")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_mpo_empty_keyword_returns_error(search):
    with pytest.raises(ValueError):
        search.search_mpo("")


def test_search_result_has_manifest_url(search):
    result = search.search_sdhk("Kung")
    assert result.records
    assert "manifest_url" in result.records[0]


def test_search_result_dataclass_fields(search):
    result = search.search_sdhk("Kung")
    assert result.keyword == "Kung"
    assert result.offset == 0
    assert result.limit == 25
    assert result.table_name == "sdhk"


def test_search_mpo_result_has_manifest_url(search):
    result = search.search_mpo("Missale")
    assert result.records
    assert "manifest_url" in result.records[0]
