"""CSV ingest functions for Filmcensur records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import FILMREG_TABLE
from .models import FilmregRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_filmreg(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest Filmregistret CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the FILMREG CSV file (semicolon-delimited, latin-1 encoded).

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
                record = FilmregRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping Filmreg row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Filmreg records parsed from {csv_path}")

    logger.info("Parsed %d Filmreg records", len(records))

    table = db.create_table(FILMREG_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
