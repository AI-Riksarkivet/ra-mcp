"""CSV ingest functions for Swedish church records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import build_fts_index

from .config import DODA_TABLE, FODELSE_TABLE, VIGSEL_TABLE
from .models import DodaRecord, FodelseRecord, VigselRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_fodelse(db: lancedb.DBConnection, csv_dir: str | Path) -> lancedb.table.Table:
    """Ingest birth (födelse) CSVs from a directory into a LanceDB table with FTS index.

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
        logger.info("Reading Födelse file: %s", csv_path.name)
        with csv_path.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = FodelseRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping Födelse row %d in %s: %s", lineno, csv_path.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        raise ValueError(f"No valid Födelse records parsed from {csv_dir}")

    logger.info("Parsed %d Födelse records from %d files", len(records), len(csv_files))

    table = db.create_table(FODELSE_TABLE, data=records, mode="overwrite")
    table = build_fts_index(db, FODELSE_TABLE)
    return table


def ingest_doda(db: lancedb.DBConnection, csv_dir: str | Path) -> lancedb.table.Table:
    """Ingest death (döda) CSVs from a directory into a LanceDB table with FTS index.

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
        logger.info("Reading Döda file: %s", csv_path.name)
        with csv_path.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = DodaRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping Döda row %d in %s: %s", lineno, csv_path.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        raise ValueError(f"No valid Döda records parsed from {csv_dir}")

    logger.info("Parsed %d Döda records from %d files", len(records), len(csv_files))

    table = db.create_table(DODA_TABLE, data=records, mode="overwrite")
    table = build_fts_index(db, DODA_TABLE)
    return table


def ingest_vigsel(db: lancedb.DBConnection, csv_dir: str | Path) -> lancedb.table.Table:
    """Ingest marriage (vigsel) CSVs from a directory into a LanceDB table with FTS index.

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
        logger.info("Reading Vigsel file: %s", csv_path.name)
        with csv_path.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = VigselRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping Vigsel row %d in %s: %s", lineno, csv_path.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        raise ValueError(f"No valid Vigsel records parsed from {csv_dir}")

    logger.info("Parsed %d Vigsel records from %d files", len(records), len(csv_files))

    table = db.create_table(VIGSEL_TABLE, data=records, mode="overwrite")
    table = build_fts_index(db, VIGSEL_TABLE)
    return table
