"""CSV ingest functions for Aktiebolag records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import BOLAG_TABLE, STYRELSE_TABLE
from .models import AktiebolagRecord, StyrelseRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def _build_styrelse_name_map(styrelse_path: str | Path) -> dict[int, list[str]]:
    """Read STYRELSEMEDLEMMAR.txt and build PostID -> list of member names.

    The file uses semicolon delimiters, latin-1 encoding, and '-' as null sentinel.
    """
    styrelse_path = Path(styrelse_path)
    result: dict[int, list[str]] = {}
    with styrelse_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            post_id_raw = (row.get("PostID", "") or "").strip().strip('"')
            if not post_id_raw or post_id_raw == "-":
                continue
            try:
                post_id = int(post_id_raw)
            except ValueError:
                continue
            surname = (row.get("Styrelsemed", "") or "").strip().strip('"')
            fornamn = (row.get("Fornamn", "") or "").strip().strip('"')
            if surname == "-":
                surname = ""
            if fornamn == "-":
                fornamn = ""
            name_parts = [p for p in [fornamn, surname] if p]
            if name_parts:
                result.setdefault(post_id, []).append(" ".join(name_parts))
    return result


def _build_bolag_name_map(bolag_path: str | Path) -> dict[int, str]:
    """Read AKTIEBOLAG.txt and build PostID -> company name lookup."""
    bolag_path = Path(bolag_path)
    result: dict[int, str] = {}
    with bolag_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            post_id_raw = (row.get("PostID", "") or "").strip().strip('"')
            if not post_id_raw or post_id_raw == "-":
                continue
            try:
                post_id = int(post_id_raw)
            except ValueError:
                continue
            namn = (row.get("Bolagets_namn", "") or "").strip().strip('"')
            if namn and namn != "-":
                result[post_id] = namn
    return result


def ingest_aktiebolag(
    db: lancedb.DBConnection,
    bolag_path: str | Path,
    styrelse_path: str | Path,
) -> tuple[lancedb.table.Table, lancedb.table.Table]:
    """Ingest Aktiebolag and Styrelsemedlemmar into LanceDB tables with FTS indexes.

    Joins STYRELSEMEDLEMMAR on PostID to enrich companies with board member names,
    and joins AKTIEBOLAG on PostID to enrich board members with company names.

    Args:
        db: LanceDB database connection.
        bolag_path: Path to AKTIEBOLAG.txt (semicolon-delimited, latin-1).
        styrelse_path: Path to STYRELSEMEDLEMMAR.txt (semicolon-delimited, latin-1).

    Returns:
        Tuple of (bolag_table, styrelse_table).

    Raises:
        ValueError: If no records could be parsed from either file.
    """
    # Build lookup maps for the join
    logger.info("Building styrelse name lookup from %s ...", styrelse_path)
    styrelse_names = _build_styrelse_name_map(styrelse_path)
    styrelse_map: dict[int, str] = {pid: ", ".join(names) for pid, names in styrelse_names.items()}
    logger.info("Loaded board member names for %d companies", len(styrelse_map))

    logger.info("Building bolag name lookup from %s ...", bolag_path)
    bolag_name_map = _build_bolag_name_map(bolag_path)
    logger.info("Loaded %d company names", len(bolag_name_map))

    # --- Ingest bolag table ---
    bolag_path = Path(bolag_path)
    bolag_records: list[dict] = []

    with bolag_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for lineno, row in enumerate(reader, start=2):
            try:
                record = AktiebolagRecord.from_csv_row(row, styrelse_map)
            except Exception as exc:
                logger.warning("Skipping Aktiebolag row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            bolag_records.append(flat)

    if not bolag_records:
        raise ValueError(f"No valid Aktiebolag records parsed from {bolag_path}")

    logger.info("Parsed %d Aktiebolag records", len(bolag_records))

    bolag_table = db.create_table(BOLAG_TABLE, data=bolag_records, mode="overwrite")
    bolag_table.create_fts_index("searchable_text", replace=True)

    # --- Ingest styrelse table ---
    styrelse_path = Path(styrelse_path)
    styrelse_records: list[dict] = []

    with styrelse_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for lineno, row in enumerate(reader, start=2):
            try:
                record = StyrelseRecord.from_csv_row(row, bolag_name_map)
            except Exception as exc:
                logger.warning("Skipping Styrelse row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            styrelse_records.append(flat)

    if not styrelse_records:
        raise ValueError(f"No valid Styrelse records parsed from {styrelse_path}")

    logger.info("Parsed %d Styrelse records", len(styrelse_records))

    styrelse_table = db.create_table(STYRELSE_TABLE, data=styrelse_records, mode="overwrite")
    styrelse_table.create_fts_index("searchable_text", replace=True)

    return bolag_table, styrelse_table
