"""Shared LanceDB spine for the dataset libraries.

One place for the ``SearchResult`` envelope, cached connections, Swedish
full-text index construction, and a correct, instrumented full-text search — so
the 13 dataset libraries share a single implementation instead of copy-pasting it
(and copy-pasting its bugs: English-stemmed Swedish text, a fake ``total_hits``
capped at ``limit + offset``, and window-and-slice pagination that drops rows).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from lancedb.index import FTS
from opentelemetry.trace import SpanKind
from pydantic import BaseModel

from ra_mcp_common.telemetry import get_meter, get_tracer


if TYPE_CHECKING:
    import lancedb


_tracer = get_tracer("ra_mcp.lancedb")
_query_counter = get_meter("ra_mcp.lancedb").create_counter("ra_mcp.lancedb.queries", unit="{query}", description="LanceDB full-text search queries")

# lancedb 0.34 exposes no count API on an FTS query, so total_hits is a true match
# count up to this bound — far above any realistic UI page, and vastly better than
# the previous len-of-a-window total that could never exceed limit + offset.
MAX_TOTAL_COUNT = 10_000

_connections: dict[str, lancedb.DBConnection] = {}
_connections_lock = threading.Lock()


class SearchResult(BaseModel):
    """One page of a dataset full-text search plus the total match count."""

    records: list[dict[str, Any]]
    total_hits: int
    keyword: str
    offset: int
    limit: int


def get_lancedb(uri: str) -> lancedb.DBConnection:
    """Return a process-cached LanceDB connection for ``uri`` (thread-safe lazy init).

    LanceDB connections are ``Send + Sync`` and have no ``close()``; caching one per
    URI for the process lifetime is the intended usage.
    """
    conn = _connections.get(uri)
    if conn is None:
        with _connections_lock:
            conn = _connections.get(uri)
            if conn is None:
                import lancedb

                conn = lancedb.connect(uri)
                _connections[uri] = conn
    return conn


def build_fts_index(db: lancedb.DBConnection, table_name: str, column: str = "searchable_text") -> None:
    """Build (or replace) a Swedish full-text index on ``table_name.column``.

    ``FTS(language="Swedish")`` applies Swedish stemming + stop-words so inflected
    queries match (``"häst"`` finds ``"hästar"`` / ``"hästen"``). The default English
    analyzer mis-stems Swedish text and silently misses inflected forms.
    """
    table = db.open_table(table_name)
    table.create_index(column, config=FTS(language="Swedish"), replace=True)


def lancedb_fts_search(
    db: lancedb.DBConnection,
    table_name: str,
    keyword: str,
    *,
    limit: int,
    offset: int = 0,
    where: str | None = None,
) -> SearchResult:
    """Full-text search returning one correctly-paginated page and a true total.

    Filters are pushed into LanceDB via ``where`` (a SQL predicate), so the total
    and the page are computed over the already-filtered result set — unlike the
    old per-dataset code which post-filtered a tiny window and reported
    ``len(window)`` (capped at ``limit + offset``) as the total.

    The ranked result set is fetched once (up to :data:`MAX_TOTAL_COUNT`) and the
    page is sliced from it. A single ranked query is used deliberately rather than
    native ``.offset()`` across separate queries: BM25 score ties reorder results
    between queries, so per-query offsets drop and duplicate rows. Slicing one
    ranked set gives both a real ``total_hits`` and stable, gap-free pagination.

    Raises:
        ValueError: if ``keyword`` is empty or whitespace.
    """
    if not keyword or not keyword.strip():
        raise ValueError("keyword must be non-empty")

    table = db.open_table(table_name)
    query: Any = table.search(keyword, query_type="fts")
    if where:
        query = query.where(where)

    with _tracer.start_as_current_span(
        f"search {table_name}",
        kind=SpanKind.CLIENT,
        attributes={"db.system.name": "lancedb", "db.collection.name": table_name},
    ) as span:
        matches = query.limit(MAX_TOTAL_COUNT).to_list()
        page = matches[offset : offset + limit]
        span.set_attribute("db.response.returned_rows", len(page))

    _query_counter.add(1, {"db.collection.name": table_name})

    return SearchResult(records=page, total_hits=len(matches), keyword=keyword, offset=offset, limit=limit)
