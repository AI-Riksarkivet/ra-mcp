"""Tests for Sjömanshus CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sjomanshus_lib.ingest import ingest_liggare, ingest_matrikel


FIXTURES = Path(__file__).parent / "fixtures"
LIGGARE_FIXTURE = FIXTURES / "liggare_sample.csv"
MATRIKEL_FIXTURE = FIXTURES / "matrikel_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_liggare(db):
    table = ingest_liggare(db, LIGGARE_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_liggare_columns(db):
    table = ingest_liggare(db, LIGGARE_FIXTURE)
    schema_names = table.schema.names
    for col in ("id", "foernamn", "efternamn1", "befattning_yrke", "fartyg", "searchable_text", "sjoemanshus"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_matrikel(db):
    table = ingest_matrikel(db, MATRIKEL_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_matrikel_columns(db):
    table = ingest_matrikel(db, MATRIKEL_FIXTURE)
    schema_names = table.schema.names
    for col in ("id", "foernamn", "efternamn1", "far", "mor", "searchable_text", "sjoemanshus"):
        assert col in schema_names, f"Missing column: {col}"
