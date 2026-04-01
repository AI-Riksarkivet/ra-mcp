"""CSV ingest functions for court records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import DOMBOKSREGISTER_TABLE, MEDELSTAD_TABLE
from .models import DomboksregisterRecord, MedelstadRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def _build_paragraf_map(paragraf_csv: str | Path) -> dict[str, dict[str, str]]:
    """Read Paragraf.csv and build a lookup dict keyed by ParagrafId.

    The CSV has quoted fields, semicolon delimiters, and latin-1 encoding.
    """
    paragraf_csv = Path(paragraf_csv)
    result: dict[str, dict[str, str]] = {}
    with paragraf_csv.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            pid = row.get("ParagrafId", "").strip().strip('"')
            if pid:
                result[pid] = row
    return result


def _build_maal_map(maal_csv: str | Path) -> dict[str, str]:
    """Read maal.csv and build a lookup dict from Loepnr to Maal_referat."""
    maal_csv = Path(maal_csv)
    result: dict[str, str] = {}
    with maal_csv.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            lopnr = (row.get("Loepnr", "") or row.get("Löpnr", "")).strip().strip('"')
            referat = (row.get("Maal_referat", "") or row.get("Mål_referat", "")).strip().strip('"')
            if lopnr:
                result[lopnr] = referat
    return result


def ingest_domboksregister(
    db: lancedb.DBConnection,
    person_csv: str | Path,
    paragraf_csv: str | Path,
) -> lancedb.table.Table:
    """Ingest Domboksregister CSVs into a LanceDB table with FTS index.

    Joins Person.csv with Paragraf.csv on ParagrafId to enrich person
    records with case date (Datum) and case type (Arende).

    Args:
        db: LanceDB database connection.
        person_csv: Path to Person.csv (semicolon-delimited, latin-1, quoted fields).
        paragraf_csv: Path to Paragraf.csv (semicolon-delimited, latin-1, quoted fields).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed.
    """
    logger.info("Building Paragraf lookup from %s ...", paragraf_csv)
    paragraf_map = _build_paragraf_map(paragraf_csv)
    logger.info("Loaded %d Paragraf entries", len(paragraf_map))

    person_csv = Path(person_csv)
    records: list[dict] = []

    with person_csv.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for lineno, row in enumerate(reader, start=2):
            try:
                record = DomboksregisterRecord.from_csv_row(row, paragraf_map)
            except Exception as exc:
                logger.warning("Skipping Domboksregister row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Domboksregister records parsed from {person_csv}")

    logger.info("Parsed %d Domboksregister records", len(records))

    table = db.create_table(DOMBOKSREGISTER_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_medelstad(
    db: lancedb.DBConnection,
    person_csv: str | Path,
    maal_csv: str | Path,
) -> lancedb.table.Table:
    """Ingest Medelstad CSVs into a LanceDB table with FTS index.

    Joins personposter.csv with maal.csv on Löpnr/Loepnr to enrich
    person records with case summary text (Maal_referat).

    Args:
        db: LanceDB database connection.
        person_csv: Path to personposter.csv (semicolon-delimited, latin-1).
        maal_csv: Path to maal.csv (semicolon-delimited, latin-1).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed.
    """
    logger.info("Building maal lookup from %s ...", maal_csv)
    maal_map = _build_maal_map(maal_csv)
    logger.info("Loaded %d maal entries", len(maal_map))

    person_csv = Path(person_csv)
    records: list[dict] = []

    with person_csv.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for lineno, row in enumerate(reader, start=2):
            try:
                record = MedelstadRecord.from_csv_row(row, maal_map)
            except Exception as exc:
                logger.warning("Skipping Medelstad row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid Medelstad records parsed from {person_csv}")

    logger.info("Parsed %d Medelstad records", len(records))

    table = db.create_table(MEDELSTAD_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
