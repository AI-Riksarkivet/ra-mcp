"""CSV ingest functions for Rosenberg records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import ROSENBERG_TABLE
from .models import RosenbergRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_rosenberg(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Rosenberg CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the Rosenberg CSV file (semicolon-delimited, latin-1 encoded).

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
                record = RosenbergRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping Rosenberg row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Rosenberg records parsed from {csv_path}")

    logger.info("Parsed %d Rosenberg records", len(records))

    table = db.create_table(ROSENBERG_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
