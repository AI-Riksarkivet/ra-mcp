"""Tests for CourtSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_court_lib.ingest import ingest_domboksregister, ingest_medelstad
from ra_mcp_court_lib.search_operations import CourtSearch


FIXTURES = Path(__file__).parent / "fixtures"
PERSON_FIXTURE = FIXTURES / "person_sample.csv"
PARAGRAF_FIXTURE = FIXTURES / "paragraf_sample.csv"
PERSONPOSTER_FIXTURE = FIXTURES / "personposter_sample.csv"
MAAL_FIXTURE = FIXTURES / "maal_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a CourtSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_domboksregister(db, PERSON_FIXTURE, PARAGRAF_FIXTURE)
    ingest_medelstad(db, PERSONPOSTER_FIXTURE, MAAL_FIXTURE)
    return CourtSearch(db)


# ---------------------------------------------------------------------------
# search_domboksregister
# ---------------------------------------------------------------------------


def test_search_domboksregister_returns_results(search):
    result = search.search_domboksregister("Persson")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_domboksregister_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_domboksregister("")


def test_search_domboksregister_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_domboksregister("   ")


def test_search_domboksregister_pagination(search):
    result = search.search_domboksregister("Persson", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_domboksregister_result_fields(search):
    result = search.search_domboksregister("Persson")
    assert result.keyword == "Persson"
    assert result.offset == 0
    assert result.limit == 25


def test_search_domboksregister_has_searchable_text(search):
    result = search.search_domboksregister("Persson")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_domboksregister_filter_roll(search):
    result = search.search_domboksregister("Persson", roll="Kärande")
    for rec in result.records:
        assert "kärande" in rec.get("roll", "").lower()


def test_search_domboksregister_filter_socken(search):
    result = search.search_domboksregister("Persson", socken="Kinnevald")
    for rec in result.records:
        assert "kinnevald" in rec.get("socken", "").lower()


def test_search_domboksregister_filter_datum_from(search):
    result = search.search_domboksregister("Persson", datum_from="1650-01-01")
    for rec in result.records:
        assert rec.get("datum", "") >= "1650-01-01"


def test_search_domboksregister_filter_datum_till(search):
    result = search.search_domboksregister("Persson", datum_till="1650-12-31")
    for rec in result.records:
        assert rec.get("datum", "") <= "1650-12-31"


def test_search_domboksregister_filter_datum_range(search):
    result = search.search_domboksregister("Persson", datum_from="1650-01-01", datum_till="1650-12-31")
    for rec in result.records:
        assert "1650-01-01" <= rec.get("datum", "") <= "1650-12-31"


def test_search_domboksregister_filter_arende(search):
    result = search.search_domboksregister("Persson", arende="Skuld")
    assert result.total_hits >= 1
    for rec in result.records:
        assert "skuld" in rec.get("arende", "").lower()


def test_search_domboksregister_filter_datum_excludes_out_of_range(search):
    result = search.search_domboksregister("Persson", datum_from="1900-01-01")
    assert result.total_hits == 0


# ---------------------------------------------------------------------------
# search_medelstad
# ---------------------------------------------------------------------------


def test_search_medelstad_returns_results(search):
    result = search.search_medelstad("Persson")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_medelstad_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_medelstad("")


def test_search_medelstad_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_medelstad("   ")


def test_search_medelstad_pagination(search):
    result = search.search_medelstad("Persson", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_medelstad_result_fields(search):
    result = search.search_medelstad("Persson")
    assert result.keyword == "Persson"
    assert result.offset == 0
    assert result.limit == 25


def test_search_medelstad_has_searchable_text(search):
    result = search.search_medelstad("Persson")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_medelstad_filter_mal_typ(search):
    result = search.search_medelstad("Persson", mal_typ="Skuld")
    for rec in result.records:
        assert "skuld" in rec.get("mal_typ", "").lower()


def test_search_medelstad_filter_norm_forsamling(search):
    result = search.search_medelstad("Persson", norm_forsamling="Listerby")
    for rec in result.records:
        assert "listerby" in rec.get("norm_forsamling", "").lower()


def test_search_medelstad_filter_datum_from(search):
    result = search.search_medelstad("Persson", datum_from="1690-01-01")
    for rec in result.records:
        assert rec.get("ting_dag", "") >= "1690-01-01"


def test_search_medelstad_filter_datum_till(search):
    result = search.search_medelstad("Persson", datum_till="1690-12-31")
    for rec in result.records:
        assert rec.get("ting_dag", "") <= "1690-12-31"


def test_search_medelstad_filter_datum_excludes_out_of_range(search):
    result = search.search_medelstad("Persson", datum_from="1900-01-01")
    assert result.total_hits == 0
