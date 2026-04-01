"""CSV ingest functions for Norrland vehicle registration records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import WINCARS_TABLE
from .models import WincarsRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_wincars(db: lancedb.DBConnection, csv_dir: str | Path) -> lancedb.table.Table:
    """Ingest Wincars vehicle registration CSVs from a directory into a LanceDB table with FTS index.

    Reads ALL .csv files from the given directory and concatenates rows into one table.

    Args:
        db: LanceDB database connection.
        csv_dir: Directory containing county CSV files (semicolon-delimited, latin-1 encoded).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from any CSV file.
    """
    csv_dir = Path(csv_dir)
    records: list[dict] = []

    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {csv_dir}")

    for csv_path in csv_files:
        logger.info("Reading Wincars file: %s", csv_path.name)
        with csv_path.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = WincarsRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping Wincars row %d in %s: %s", lineno, csv_path.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        raise ValueError(f"No valid Wincars records parsed from {csv_dir}")

    logger.info("Parsed %d Wincars records from %d files", len(records), len(csv_files))

    table = db.create_table(WINCARS_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
