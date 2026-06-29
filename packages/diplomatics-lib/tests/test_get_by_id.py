"""Tests for single-record lookup by ID."""

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


def test_get_sdhk_by_id_found(search):
    row = search.get_sdhk_by_id(1)
    assert row is not None
    assert row["id"] == 1


def test_get_sdhk_by_id_not_found(search):
    row = search.get_sdhk_by_id(99999)
    assert row is None


def test_get_mpo_by_id_found(search):
    row = search.get_mpo_by_id(1)
    assert row is not None
    assert row["id"] == 1


def test_get_mpo_by_id_not_found(search):
    row = search.get_mpo_by_id(99999)
    assert row is None
