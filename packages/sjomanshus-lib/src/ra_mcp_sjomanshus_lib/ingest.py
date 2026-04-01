"""CSV ingest functions for Sjömanshus records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import LIGGARE_TABLE, MATRIKEL_TABLE
from .models import LiggareRecord, MatrikelRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_liggare(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Liggare CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the Liggare CSV file (semicolon-delimited, latin-1 encoded).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from the CSV.
    """
    csv_path = Path(csv_path)
    records: list[dict] = []

    with csv_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for lineno, row in enumerate(reader, start=2):
            try:
                record = LiggareRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping Liggare row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Liggare records parsed from {csv_path}")

    logger.info("Parsed %d Liggare records", len(records))

    table = db.create_table(LIGGARE_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_matrikel(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Matrikel CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the Matrikel CSV file (semicolon-delimited, latin-1 encoded).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from the CSV.
    """
    csv_path = Path(csv_path)
    records: list[dict] = []

    with csv_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for lineno, row in enumerate(reader, start=2):
            try:
                record = MatrikelRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping Matrikel row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Matrikel records parsed from {csv_path}")

    logger.info("Parsed %d Matrikel records", len(records))

    table = db.create_table(MATRIKEL_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
