"""Tests for Rosenberg CSV ingest into LanceDB."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_rosenberg_lib.ingest import ingest_rosenberg


FIXTURES = Path(__file__).parent / "fixtures"
ROSENBERG_FIXTURE = FIXTURES / "rosenberg_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_rosenberg(db):
    table = ingest_rosenberg(db, ROSENBERG_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_rosenberg_columns(db):
    table = ingest_rosenberg(db, ROSENBERG_FIXTURE)
    schema_names = table.schema.names
    for col in ("post_id", "plats", "forsamling", "harad", "lan", "beskrivning", "searchable_text", "gastgifveri", "grufva"):
        assert col in schema_names, f"Missing column: {col}"
