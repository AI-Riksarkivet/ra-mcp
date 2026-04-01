"""CSV ingest functions for women's suffrage records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import FKPR_TABLE, ROSTRATT_TABLE
from .models import FKPRRecord, RostrattRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_rostratt(db: lancedb.DBConnection, csv_dir: str | Path) -> lancedb.table.Table:
    """Ingest Rösträtt CSVs from a directory into a LanceDB table with FTS index.

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
        logger.info("Reading Rösträtt file: %s", csv_path.name)
        with csv_path.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = RostrattRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping Rösträtt row %d in %s: %s", lineno, csv_path.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        raise ValueError(f"No valid Rösträtt records parsed from {csv_dir}")

    logger.info("Parsed %d Rösträtt records from %d files", len(records), len(csv_files))

    table = db.create_table(ROSTRATT_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_fkpr(db: lancedb.DBConnection, csv_path: str | Path) -> lancedb.table.Table:
    """Ingest FKPR CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the FKPR CSV file (semicolon-delimited, latin-1 encoded).

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
                record = FKPRRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping FKPR row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid FKPR records parsed from {csv_path}")

    logger.info("Parsed %d FKPR records", len(records))

    table = db.create_table(FKPR_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
