"""Tests for single-record lookup by ID."""

from ra_mcp_diplomatics_lib.search_operations import DiplomaticsSearch


class FakeTable:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def filter(self, expr):
        return _FilteredQuery(self._rows, expr)


class _FilteredQuery:
    def __init__(self, rows, expr):
        self._rows = rows
        self._expr = expr

    def limit(self, n):
        self._limit = n
        return self

    def to_list(self):
        target_id = int(self._expr.split("=")[1].strip())
        return [r for r in self._rows if r.get("id") == target_id][:self._limit]


class FakeDB:
    def __init__(self, tables: dict[str, FakeTable]):
        self._tables = tables

    def open_table(self, name):
        return self._tables[name]


SDHK_ROW = {
    "id": 85,
    "title": "SDHK nr 85",
    "author": "Knut Eriksson",
    "manifest_url": "https://lbiiif.riksarkivet.se/sdhk!85/manifest",
    "has_manifest": True,
}

MPO_ROW = {
    "id": 1,
    "manuscript_type": "Missale",
    "manifest_url": "https://lbiiif.riksarkivet.se/arkis!R1000001/manifest",
}


def test_get_sdhk_by_id_found():
    db = FakeDB({"sdhk": FakeTable([SDHK_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_sdhk_by_id(85)
    assert row is not None
    assert row["id"] == 85
    assert row["author"] == "Knut Eriksson"


def test_get_sdhk_by_id_not_found():
    db = FakeDB({"sdhk": FakeTable([SDHK_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_sdhk_by_id(99999)
    assert row is None


def test_get_mpo_by_id_found():
    db = FakeDB({"mpo": FakeTable([MPO_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_mpo_by_id(1)
    assert row is not None
    assert row["manuscript_type"] == "Missale"


def test_get_mpo_by_id_not_found():
    db = FakeDB({"mpo": FakeTable([MPO_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_mpo_by_id(99999)
    assert row is None
