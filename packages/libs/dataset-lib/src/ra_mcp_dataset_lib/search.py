"""Shared LanceDB spine for the dataset libraries.

One place for the ``SearchResult`` envelope, cached connections, Swedish
full-text index construction, and a correct, instrumented full-text search — so
the 13 dataset libraries share a single implementation instead of copy-pasting it
(and copy-pasting its bugs: English-stemmed Swedish text, a fake ``total_hits``
capped at ``limit + offset``, and window-and-slice pagination that drops rows).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from lancedb.index import FTS, Bitmap, BTree
from opentelemetry.trace import SpanKind, StatusCode
from pydantic import BaseModel

from ra_mcp_common.telemetry import get_meter, get_tracer, mark_span_error, record_span_exception


if TYPE_CHECKING:
    import lancedb


logger = logging.getLogger("ra_mcp.lancedb")
_tracer = get_tracer("ra_mcp.lancedb")
_meter = get_meter("ra_mcp.lancedb")
# RED metrics for the busiest tool surface (13 datasets + the pdf guide search).
_query_counter = _meter.create_counter("ra_mcp.lancedb.queries", unit="{query}", description="LanceDB full-text search queries (attempted)")
_error_counter = _meter.create_counter("ra_mcp.lancedb.errors", unit="{error}", description="LanceDB full-text search failures")
_query_duration = _meter.create_histogram("ra_mcp.lancedb.query.duration", unit="s", description="LanceDB full-text search duration")
# Behavioural signal: total matches per search, by dataset. Its zero bucket is
# "searches that returned nothing" — what users looked for but the data can't
# answer (unmet demand). The actual terms live on the span (db.query.text).
_results_histogram = _meter.create_histogram("ra_mcp.lancedb.results", unit="{hit}", description="Total matches per LanceDB search")

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


def build_fts_index(db: lancedb.DBConnection, table_name: str, column: str = "searchable_text") -> lancedb.table.Table:
    """Build (or replace) a Swedish full-text index on ``table_name.column``.

    ``FTS(language="Swedish")`` applies Swedish stemming + stop-words so inflected
    queries match (``"häst"`` finds ``"hästar"`` / ``"hästen"``). The default English
    analyzer mis-stems Swedish text and silently misses inflected forms.

    Returns the freshly-opened table handle that carries the new index. A handle
    opened before the index (e.g. the one ``create_table`` returned during ingest)
    does not see it and would fail a full-text search, so ingest should return
    *this* handle rather than its pre-index one.
    """
    table = db.open_table(table_name)
    # max_token_length is raised from the lancedb default of 40: long Swedish
    # compound words (common in historical administrative/legal text) would
    # otherwise exceed it and be dropped entirely, becoming unsearchable.
    table.create_index(column, config=FTS(language="Swedish", max_token_length=64), replace=True)
    return table


def build_scalar_indexes(
    db: lancedb.DBConnection,
    table_name: str,
    *,
    btree: Sequence[str] = (),
    bitmap: Sequence[str] = (),
) -> lancedb.table.Table:
    """Build scalar indexes on the columns a dataset filters on, so ``.where()``
    predicate push-down is an index lookup instead of a full scan of the column
    over (often remote) object storage.

    - ``btree``: ordered columns used in equality or range predicates — ids, years,
      dates (``id = X``, ``birth_year >= 1850``). A get-by-id or a bounded-range
      filter becomes a page-level lookup instead of scanning the whole column.
    - ``bitmap``: low-cardinality categoricals used in equality predicates
      (``gender = 'm'``), where a per-value bitmap beats a btree.

    Substring filters (:func:`text_contains` → ``lower(col) LIKE '%v%'``) are
    deliberately left unindexed: a leading-wildcard ``LIKE`` cannot use a
    BTree/Bitmap and the lancedb 0.34 ``NGRAM`` index (which would suit substring
    search) is not available in this pin, so those columns gain nothing here.

    Mirrors :func:`build_fts_index` — call it once during ingest, after the table
    is built, then return this handle. Building an index is an in-place mutation of
    the on-disk dataset, so this belongs in the ingest/publish path (indexes bake
    into the next snapshot), never against already-published live data.
    """
    table = db.open_table(table_name)
    for column in btree:
        table.create_index(column, config=BTree(), replace=True)
    for column in bitmap:
        table.create_index(column, config=Bitmap(), replace=True)
    return table


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
    # Guard paging centrally so every dataset tool inherits it: without this a
    # negative offset or limit < 1 slices matches[] into an empty/partial window
    # while total_hits stays nonzero, so the formatter misreports "no results" or
    # emits a broken "offset=-N" pagination footer.
    if offset < 0:
        raise ValueError(f"offset must be >= 0 (got {offset})")
    if limit < 1:
        raise ValueError(f"limit must be >= 1 (got {limit})")

    table = db.open_table(table_name)
    query: Any = table.search(keyword, query_type="fts")
    if where:
        query = query.where(where)
    # The tables are built once (create_table + create_index) and never appended
    # to, so there is no unindexed data — fast_search skips the redundant flat
    # search of unindexed rows with no loss of results.
    query = query.fast_search()

    attrs = {"db.collection.name": table_name}
    # The search term + filter go on the span (high-cardinality → span-only), so an
    # analyst can answer "what are people searching for in each dataset?" and
    # "which filters do they apply?" — the behavioural intent behind each request.
    span_attrs = {"db.system.name": "lancedb", "db.collection.name": table_name, "db.query.text": keyword}
    if where:
        span_attrs["db.query.filter"] = where
    with _tracer.start_as_current_span(f"search {table_name}", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
        start = time.perf_counter()
        try:
            matches = query.limit(MAX_TOTAL_COUNT).to_list()
        except Exception as e:
            span.set_status(StatusCode.ERROR, f"{type(e).__name__}: {e}")
            record_span_exception(logger, e)  # also sets error.type on the span
            _error_counter.add(1, {**attrs, "error.type": type(e).__name__})
            raise
        finally:
            # Count attempts (success + failure) and record latency — so error-rate
            # and p95/p99 dashboards work, not just a success-only counter.
            _query_duration.record(time.perf_counter() - start, attrs)
            _query_counter.add(1, attrs)
        total = len(matches)
        page = matches[offset : offset + limit]
        # Behavioural signals: total = how well the data answered this search
        # (0 = unmet demand); returned_rows = the page actually shown.
        span.set_attribute("db.response.total_hits", total)
        span.set_attribute("db.response.returned_rows", len(page))
        _results_histogram.record(total, attrs)

    return SearchResult(records=page, total_hits=total, keyword=keyword, offset=offset, limit=limit)


# --- SQL predicate builders ---------------------------------------------------
# The dataset libraries express typed filters (a company name, a year range, a
# gender) as LanceDB ``.where()`` predicates so filtering happens inside the
# query (pre-filter, before BM25) instead of in a Python loop over a truncated
# window. These helpers build the SQL fragments in one place with correct
# quoting, so the escaping isn't re-implemented (and mis-implemented) 13 times.


def _sql_str(value: str) -> str:
    """Quote a Python string as a SQL string literal (single quotes doubled)."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _lit(value: str | int) -> str:
    """Render a scalar as a SQL literal — quoted for str, bare for int."""
    return str(value) if isinstance(value, int) else _sql_str(value)


# Column names are emitted bare, not double-quoted: LanceDB's filter parser reads
# a double-quoted "col" as a string LITERAL (SQLite-style), not an identifier, so
# quoting silently matches nothing. The dataset columns are all simple snake_case
# identifiers, which bare form handles correctly.


def text_contains(column: str, value: str) -> str:
    """Case-insensitive substring predicate: ``lower(col) LIKE '%value%'``.

    LIKE wildcards in ``value`` (``%`` ``_`` ``\\``) are escaped so a literal
    ``%`` in the filter matches a literal ``%``, not "anything".
    """
    needle = value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"lower({column}) LIKE {_sql_str(f'%{needle}%')} ESCAPE '\\'"


def equals(column: str, value: str | int) -> str:
    """Exact-match predicate: ``col = value``."""
    return f"{column} = {_lit(value)}"


def at_least(column: str, value: str | int) -> str:
    """Lower-bound predicate: ``col >= value`` (NULLs are excluded, as in SQL)."""
    return f"{column} >= {_lit(value)}"


def at_most(column: str, value: str | int) -> str:
    """Upper-bound predicate: ``col <= value`` (NULLs are excluded, as in SQL)."""
    return f"{column} <= {_lit(value)}"


def any_of(*predicates: str) -> str:
    """OR-combine predicates into one parenthesised predicate."""
    return "(" + " OR ".join(predicates) + ")"


def combine(*predicates: str | None) -> str | None:
    """AND-combine predicates, dropping ``None`` (an unset filter).

    Returns ``None`` when nothing is set, which ``lancedb_fts_search`` treats as
    "no ``where`` clause".
    """
    parts = [p for p in predicates if p]
    if not parts:
        return None
    return " AND ".join(parts)


# --- shared MCP-handler / formatter scaffold ----------------------------------
# Every dataset MCP wraps lancedb_fts_search in the same shape: guard an empty
# keyword, then render the SearchResult page with an identical envelope (no-results
# / paginated-past-end messages, a "showing N of M records (offset K)" header, a
# "More results ... offset=" footer). Only the per-dataset label and per-record
# rendering differ. These own the shared parts so the ~20 dataset formatters and
# their keyword guards stop being copy-paste.


def require_keyword(keyword: str, example: str) -> str | None:
    """Validate a search keyword; return an error string (and mark the span ERROR)
    when it is empty/blank, else ``None``.

    Usage in a handler: ``if err := require_keyword(keyword, "'Wallenberg'"): return err``.
    ``example`` is a dataset-specific sample term shown in the message.
    """
    if not keyword or not keyword.strip():
        mark_span_error("keyword must not be empty", error_type="validation")
        return f"Error: keyword must not be empty. Provide a search term, e.g. {example}."
    return None


def require_ordered_range[T: (int, str)](low: T | None, high: T | None, label: str) -> str | None:
    """Validate an optional ``[low, high]`` filter range; return an error string
    (and mark the span ERROR) when it is inverted, else ``None``.

    Both bounds set with ``low > high`` builds an unsatisfiable ``>= low AND <= high``
    predicate, which silently returns "no results" instead of flagging the swapped
    inputs. Works for years (int) and ISO date strings (which compare correctly
    lexicographically). ``None`` for either bound means "unbounded on that side".

    Usage in a handler: ``if err := require_ordered_range(year_min, year_max, "birth year"): return err``.
    """
    if low is not None and high is not None and low > high:
        mark_span_error(f"{label} range inverted: {low} > {high}", error_type="validation")
        return f"Error: {label} range is inverted — from/min ({low}) must be <= to/max ({high}). Swap the bounds."
    return None


def format_results(
    result: SearchResult,
    *,
    label: str,
    render_record: Callable[[dict[str, Any], list[str]], None],
) -> str:
    """Render a dataset :class:`SearchResult` page as the standard plain-text block.

    Owns the envelope shared by every dataset formatter — the no-results and
    paginated-past-end messages, the ``"{label} search results ... showing N of M
    records (offset K)"`` header, and the ``"More results ... offset="`` footer.
    ``label`` names the dataset in those messages (e.g. ``"SBL"``, ``"Board
    member"``); ``render_record(rec, lines)`` appends one record's lines and is the
    only genuinely per-dataset part.
    """
    if not result.records:
        if result.offset > 0:
            return f"No more {label} results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No {label} results found for '{result.keyword}'."

    lines: list[str] = [
        f"{label} search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})",
        "",
    ]
    for rec in result.records:
        render_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)
