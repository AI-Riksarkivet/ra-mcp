"""CSV ingest functions for Specialsök datasets into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import FANGRULLOR_TABLE, FLYGVAPEN_TABLE, KURHUSET_TABLE, PRESS_TABLE, VIDEO_TABLE
from .models import (
    FANGRULLOR_FIELDNAMES,
    FangrullorRecord,
    FlygvapenRecord,
    KurhusetRecord,
    PressRecord,
    VideoRecord,
)


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def _ingest_simple(
    db: lancedb.DBConnection,
    csv_path: str | Path,
    table_name: str,
    record_cls: type,
    *,
    fieldnames: list[str] | None = None,
) -> lancedb.table.Table:
    """Generic ingest: read CSV, parse records, create FTS-indexed table.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the CSV file.
        table_name: Name of the LanceDB table to create.
        record_cls: Pydantic model class with from_csv_row and searchable_text.
        fieldnames: Optional list of column names (for header-less CSVs).

    Returns:
        The created LanceDB table.
    """
    csv_path = Path(csv_path)
    records: list[dict] = []

    with csv_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"', fieldnames=fieldnames)
        for lineno, row in enumerate(reader, start=2):
            try:
                record = record_cls.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping %s row %d: %s", table_name, lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        msg = f"No valid {table_name} records parsed from {csv_path}"
        raise ValueError(msg)

    logger.info("Parsed %d %s records", len(records), table_name)

    table = db.create_table(table_name, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_flygvapen(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Flygvapenhaverier CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the flygvapenhaverier CSV (semicolon-delimited, latin-1).

    Returns:
        The created LanceDB table.
    """
    return _ingest_simple(db, csv_path, FLYGVAPEN_TABLE, FlygvapenRecord)


def ingest_fangrullor(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Fångrullor CSV into a LanceDB table with FTS index.

    The CSV has NO header row. Column names are assigned manually.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the fångrullor CSV (semicolon-delimited, latin-1, no header).

    Returns:
        The created LanceDB table.
    """
    return _ingest_simple(db, csv_path, FANGRULLOR_TABLE, FangrullorRecord, fieldnames=FANGRULLOR_FIELDNAMES)


def ingest_kurhuset(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Kurhuset CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the kurhuset CSV (semicolon-delimited, latin-1, Swedish headers).

    Returns:
        The created LanceDB table.
    """
    return _ingest_simple(db, csv_path, KURHUSET_TABLE, KurhusetRecord)


def ingest_press(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Presskonferenser CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the presskonferenser CSV (semicolon-delimited, latin-1).

    Returns:
        The created LanceDB table.
    """
    return _ingest_simple(db, csv_path, PRESS_TABLE, PressRecord)


def ingest_video(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Videobutiker CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the videobutiker CSV (semicolon-delimited, latin-1).

    Returns:
        The created LanceDB table.
    """
    return _ingest_simple(db, csv_path, VIDEO_TABLE, VideoRecord)
