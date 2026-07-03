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

from ra_mcp_dataset_lib import build_fts_index, lancedb_fts_search


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
