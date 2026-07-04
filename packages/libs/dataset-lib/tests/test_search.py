"""Tests for the shared LanceDB spine: Swedish FTS, real total + native
pagination, filter push-down, and the CLIENT span. These pin the fixes for the
bugs the audit found (English-stemmed Swedish, fake total_hits, window-and-slice
pagination) and would fail against the old per-dataset implementation.
"""

import lancedb
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ra_mcp_dataset_lib import (
    any_of,
    at_least,
    at_most,
    build_fts_index,
    build_scalar_indexes,
    combine,
    equals,
    lancedb_fts_search,
    text_contains,
)


@pytest.fixture
def db(tmp_path):
    """A tiny table: 40 rows whose text uses inflected 'häst' forms (gender m/f
    split 20/20), plus 10 non-matching 'katt' rows."""
    conn = lancedb.connect(str(tmp_path / "db"))
    rows = [{"id": i, "gender": "m" if i % 2 else "f", "searchable_text": f"hästar och hästen nummer {i}"} for i in range(40)]
    rows += [{"id": i, "gender": "f", "searchable_text": f"en katt nummer {i}"} for i in range(40, 50)]
    conn.create_table("t", data=rows, mode="overwrite")
    build_fts_index(conn, "t")
    return conn


@pytest.fixture
def spans():
    exporter = InMemorySpanExporter()
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        current.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    exporter.clear()
    yield exporter
    exporter.clear()


def test_build_scalar_indexes_builds_btree_and_bitmap_and_keeps_fts_correct(tmp_path):
    # BTree on ordered columns (id/year), Bitmap on the low-cardinality gender —
    # and a filtered FTS query must still return the right rows with the scalar
    # indexes present (the ingest path builds FTS then these).
    conn = lancedb.connect(str(tmp_path / "db"))
    rows = [{"id": i, "gender": "m" if i % 2 else "f", "year": 1800 + i, "searchable_text": f"hästen {i}"} for i in range(20)]
    conn.create_table("t", data=rows, mode="overwrite")
    build_fts_index(conn, "t")
    table = build_scalar_indexes(conn, "t", btree=["id", "year"], bitmap=["gender"])

    index_types = {ix.name: ix.index_type for ix in table.list_indices()}
    assert index_types.get("id_idx") == "BTree"
    assert index_types.get("year_idx") == "BTree"
    assert index_types.get("gender_idx") == "Bitmap"

    result = lancedb_fts_search(conn, "t", "häst", limit=50, where="gender = 'm'")
    assert result.records and all(r["gender"] == "m" for r in result.records)


def test_build_fts_index_returns_searchable_handle(tmp_path):
    # The handle build_fts_index returns must carry the index — a handle opened
    # (or created) before the index does not see it and fails FTS. Ingest returns
    # this handle, so a direct FTS search on it must work.
    conn = lancedb.connect(str(tmp_path / "db"))
    conn.create_table("t", data=[{"id": i, "searchable_text": f"hästen {i}"} for i in range(5)], mode="overwrite")
    table = build_fts_index(conn, "t")
    rows = table.search("häst", query_type="fts").limit(10).to_list()
    assert len(rows) == 5


def test_swedish_fts_matches_inflections(db):
    # "häst" (a form absent from the text) matches "hästar"/"hästen" via Swedish
    # stemming — the English default analyzer would miss these.
    result = lancedb_fts_search(db, "t", "häst", limit=100)
    assert result.total_hits == 40
    assert all("häst" in r["searchable_text"] for r in result.records)


def test_total_hits_is_the_real_count_not_the_page_length(db):
    # 40 matches, page of 10 → total_hits must be 40, not <=10 (the old len(window) bug).
    result = lancedb_fts_search(db, "t", "häst", limit=10, offset=0)
    assert len(result.records) == 10
    assert result.total_hits == 40


def test_pagination_is_stable_and_gap_free(db):
    # Paging through the ranked set must cover all 40 with no gaps or duplicates
    # (the old window-and-slice code, and naive per-query .offset(), both fail this).
    seen: set[int] = set()
    for off in range(0, 40, 10):
        page = lancedb_fts_search(db, "t", "häst", limit=10, offset=off)
        seen.update(r["id"] for r in page.records)
    assert len(seen) == 40


def test_filtered_deep_page_pushes_predicate_down(db):
    # gender='m' is 20 of the 40; total + rows must reflect the filtered set.
    result = lancedb_fts_search(db, "t", "häst", limit=5, offset=10, where="gender = 'm'")
    assert result.total_hits == 20
    assert all(r["gender"] == "m" for r in result.records)


def test_empty_keyword_raises(db):
    with pytest.raises(ValueError, match="non-empty"):
        lancedb_fts_search(db, "t", "   ", limit=10)


def test_emits_lancedb_client_span(db, spans):
    lancedb_fts_search(db, "t", "häst", limit=5)
    matched = [s for s in spans.get_finished_spans() if s.name == "search t"]
    assert matched, "no 'search t' CLIENT span emitted"
    assert matched[0].attributes["db.system.name"] == "lancedb"


def test_span_captures_behavioural_signals(db, spans):
    # The span carries what an analyst needs: the search TERM (intent), the FILTER,
    # and the total hit count (engagement / unmet demand).
    lancedb_fts_search(db, "t", "häst", limit=5, where="gender = 'm'")
    span = next(s for s in spans.get_finished_spans() if s.name == "t search" or s.name == "search t")
    a = span.attributes
    assert a["db.query.text"] == "häst"
    assert a["db.query.filter"] == "gender = 'm'"
    assert a["db.response.total_hits"] == 20  # gender='m' half of the 40 häst rows


# --- predicate builders: proven end-to-end against a real table ---------------


def test_equals_predicate_pushes_down(db):
    result = lancedb_fts_search(db, "t", "häst", limit=100, where=equals("gender", "m"))
    assert result.total_hits == 20
    assert all(r["gender"] == "m" for r in result.records)


def test_range_predicates_bound_the_set(db):
    # ids 0..39 match 'häst'; keep 10 <= id <= 19 → 10 rows.
    where = combine(at_least("id", 10), at_most("id", 19))
    result = lancedb_fts_search(db, "t", "häst", limit=100, where=where)
    assert result.total_hits == 10
    assert all(10 <= r["id"] <= 19 for r in result.records)


def test_text_contains_is_case_insensitive_substring(db):
    # searchable_text is "hästar och hästen nummer N"; match the 'nummer' substring
    # case-insensitively via lower(col) LIKE '%nummer%'.
    result = lancedb_fts_search(db, "t", "häst", limit=100, where=text_contains("searchable_text", "NUMMER"))
    assert result.total_hits == 40


def test_any_of_ors_predicates(db):
    where = any_of(equals("id", 3), equals("id", 7))
    result = lancedb_fts_search(db, "t", "häst", limit=100, where=where)
    assert {r["id"] for r in result.records} == {3, 7}


def test_combine_drops_none_and_returns_none_when_empty():
    assert combine(None, None) is None
    assert combine(equals("gender", "m"), None) == "gender = 'm'"


def test_text_contains_escapes_quotes_and_wildcards(db):
    # A value with a single quote and a LIKE wildcard must not error or over-match;
    # no row contains it, so the (valid) predicate yields zero hits.
    result = lancedb_fts_search(db, "t", "häst", limit=100, where=text_contains("searchable_text", "o'brien %"))
    assert result.total_hits == 0
