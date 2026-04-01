"""CSV ingest functions for SBL records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import SBL_TABLE
from .models import SBLRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_sbl(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest SBL CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the SBL CSV file (semicolon-delimited, latin-1 encoded).

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
                record = SBLRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping SBL row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid SBL records parsed from {csv_path}")

    logger.info("Parsed %d SBL records", len(records))

    table = db.create_table(SBL_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
