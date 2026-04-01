"""Tests for SjomanshusSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sjomanshus_lib.ingest import ingest_liggare, ingest_matrikel
from ra_mcp_sjomanshus_lib.search_operations import SjomanshusSearch


FIXTURES = Path(__file__).parent / "fixtures"
LIGGARE_FIXTURE = FIXTURES / "liggare_sample.csv"
MATRIKEL_FIXTURE = FIXTURES / "matrikel_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return a SjomanshusSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_liggare(db, LIGGARE_FIXTURE)
    ingest_matrikel(db, MATRIKEL_FIXTURE)
    return SjomanshusSearch(db)


# ---------------------------------------------------------------------------
# search_liggare
# ---------------------------------------------------------------------------


def test_search_liggare_returns_results(search):
    result = search.search_liggare("Pettersson")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_liggare_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_liggare("")


def test_search_liggare_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_liggare("   ")


def test_search_liggare_pagination(search):
    result = search.search_liggare("Pettersson", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_liggare_result_fields(search):
    result = search.search_liggare("Pettersson")
    assert result.keyword == "Pettersson"
    assert result.offset == 0
    assert result.limit == 25


def test_search_liggare_has_searchable_text(search):
    result = search.search_liggare("Pettersson")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_liggare_filter_befattning(search):
    result = search.search_liggare("Pettersson", befattning="Matros")
    for rec in result.records:
        assert "matros" in rec.get("befattning_yrke", "").lower()


def test_search_liggare_filter_sjoemanshus(search):
    result = search.search_liggare("Pettersson", sjoemanshus="Karlskrona")
    for rec in result.records:
        assert "karlskrona" in rec.get("sjoemanshus", "").lower()


# ---------------------------------------------------------------------------
# search_matrikel
# ---------------------------------------------------------------------------


def test_search_matrikel_returns_results(search):
    result = search.search_matrikel("Pettersson")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_matrikel_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_matrikel("")


def test_search_matrikel_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_matrikel("   ")


def test_search_matrikel_pagination(search):
    result = search.search_matrikel("Pettersson", limit=1)
    assert len(result.records) <= 1
    assert result.limit == 1


def test_search_matrikel_result_fields(search):
    result = search.search_matrikel("Pettersson")
    assert result.keyword == "Pettersson"
    assert result.offset == 0
    assert result.limit == 25


def test_search_matrikel_has_searchable_text(search):
    result = search.search_matrikel("Pettersson")
    assert result.records
    assert "searchable_text" in result.records[0]


def test_search_matrikel_filter_sjoemanshus(search):
    result = search.search_matrikel("Pettersson", sjoemanshus="Karlskrona")
    for rec in result.records:
        assert "karlskrona" in rec.get("sjoemanshus", "").lower()
