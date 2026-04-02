"""Tests for court records CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_court_lib.ingest import ingest_domboksregister, ingest_medelstad


FIXTURES = Path(__file__).parent / "fixtures"
PERSON_FIXTURE = FIXTURES / "person_sample.csv"
PARAGRAF_FIXTURE = FIXTURES / "paragraf_sample.csv"
PERSONPOSTER_FIXTURE = FIXTURES / "personposter_sample.csv"
MAAL_FIXTURE = FIXTURES / "maal_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


# ---------------------------------------------------------------------------
# Domboksregister ingest
# ---------------------------------------------------------------------------


def test_ingest_domboksregister(db):
    table = ingest_domboksregister(db, PERSON_FIXTURE, PARAGRAF_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_domboksregister_columns(db):
    table = ingest_domboksregister(db, PERSON_FIXTURE, PARAGRAF_FIXTURE)
    schema_names = table.schema.names
    for col in ("id", "fnamn", "enamn", "roll", "socken", "datum", "arende", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_domboksregister_join(db):
    table = ingest_domboksregister(db, PERSON_FIXTURE, PARAGRAF_FIXTURE)
    rows = table.to_arrow().to_pylist()
    row_p001 = next(r for r in rows if r["paragraf_id"] == "P001")
    assert row_p001["datum"] == "1650-03-12"
    assert row_p001["arende"] == "Skuld och fordran"


# ---------------------------------------------------------------------------
# Medelstad ingest
# ---------------------------------------------------------------------------


def test_ingest_medelstad(db):
    table = ingest_medelstad(db, PERSONPOSTER_FIXTURE, MAAL_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_medelstad_columns(db):
    table = ingest_medelstad(db, PERSONPOSTER_FIXTURE, MAAL_FIXTURE)
    schema_names = table.schema.names
    for col in ("lopnr", "norm_fornamn", "norm_efternamn", "mal_typ", "mal_referat", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_medelstad_join(db):
    table = ingest_medelstad(db, PERSONPOSTER_FIXTURE, MAAL_FIXTURE)
    rows = table.to_arrow().to_pylist()
    row_1 = next(r for r in rows if r["lopnr"] == 1)
    assert "Anders Persson" in row_1["mal_referat"]
