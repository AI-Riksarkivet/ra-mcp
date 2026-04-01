"""Tests for SpecialsokSearch over ingested sample data."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_specialsok_lib.ingest import (
    ingest_fangrullor,
    ingest_flygvapen,
    ingest_kurhuset,
    ingest_press,
    ingest_video,
)
from ra_mcp_specialsok_lib.search_operations import SpecialsokSearch


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def search(tmp_path):
    """Return a SpecialsokSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_flygvapen(db, FIXTURES / "flygvapen_sample.csv")
    ingest_fangrullor(db, FIXTURES / "fangrullor_sample.csv")
    ingest_kurhuset(db, FIXTURES / "kurhuset_sample.csv")
    ingest_press(db, FIXTURES / "press_sample.csv")
    ingest_video(db, FIXTURES / "video_sample.csv")
    return SpecialsokSearch(db)


# ---------------------------------------------------------------------------
# Flygvapenhaverier
# ---------------------------------------------------------------------------


def test_search_flygvapen_returns_results(search):
    result = search.search_flygvapen("Draken")
    assert result.total_hits >= 1


def test_search_flygvapen_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_flygvapen("")


def test_search_flygvapen_pagination(search):
    result = search.search_flygvapen("Draken", limit=1)
    assert len(result.records) <= 1


def test_search_flygvapen_filter_fpl_typ(search):
    result = search.search_flygvapen("kraschade", fpl_typ="J 35")
    for rec in result.records:
        assert "j 35" in rec.get("fpl_typ", "").lower()


# ---------------------------------------------------------------------------
# Fångrullor
# ---------------------------------------------------------------------------


def test_search_fangrullor_returns_results(search):
    result = search.search_fangrullor("Andersson")
    assert result.total_hits >= 1


def test_search_fangrullor_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_fangrullor("")


def test_search_fangrullor_filter_brott(search):
    result = search.search_fangrullor("Andersson", brott="Stöld")
    for rec in result.records:
        assert "stöld" in rec.get("brott", "").lower()


# ---------------------------------------------------------------------------
# Kurhuset
# ---------------------------------------------------------------------------


def test_search_kurhuset_returns_results(search):
    result = search.search_kurhuset("Syfilis")
    assert result.total_hits >= 1


def test_search_kurhuset_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_kurhuset("")


def test_search_kurhuset_filter_sjukdom(search):
    result = search.search_kurhuset("Maria", sjukdom="Syfilis")
    for rec in result.records:
        assert "syfilis" in rec.get("sjukdom", "").lower()


# ---------------------------------------------------------------------------
# Presskonferenser
# ---------------------------------------------------------------------------


def test_search_press_returns_results(search):
    result = search.search_press("EU")
    assert result.total_hits >= 1


def test_search_press_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_press("")


def test_search_press_filter_aar(search):
    result = search.search_press("EU", aar="1995")
    for rec in result.records:
        assert "1995" in rec.get("aar", "")


# ---------------------------------------------------------------------------
# Videobutiker
# ---------------------------------------------------------------------------


def test_search_video_returns_results(search):
    result = search.search_video("Stockholm")
    assert result.total_hits >= 1


def test_search_video_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search_video("")


def test_search_video_filter_laen(search):
    result = search.search_video("Video", laen="Stockholm")
    for rec in result.records:
        assert "stockholm" in rec.get("laen", "").lower()


def test_search_video_filter_kommun(search):
    result = search.search_video("Video", kommun="Stockholm")
    for rec in result.records:
        assert "stockholm" in rec.get("kommun", "").lower()
