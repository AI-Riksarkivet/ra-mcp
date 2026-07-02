"""CSV ingest functions for SJ railway records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import FIRA_TABLE, JUDA_TABLE
from .models import RITNING_FIELDNAMES, JudaRecord, RitningRecord


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def _load_lookup(path: str | Path) -> dict[str, str]:
    """Read a KOD;KODFOERKLARING lookup CSV into a dict.

    Args:
        path: Path to the lookup CSV (semicolon-delimited, latin-1).

    Returns:
        Mapping from KOD to KODFOERKLARING.
    """
    path = Path(path)
    result: dict[str, str] = {}
    with path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            kod = (row.get("KOD", "") or "").strip().strip('"')
            forklaring = (row.get("KODFOERKLARING", "") or "").strip().strip('"')
            if kod:
                result[kod] = forklaring
    return result


def ingest_juda(
    db: lancedb.DBConnection,
    csv_dir: str | Path,
) -> lancedb.table.Table:
    """Ingest JUDA CSV files (JDA*.csv) into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_dir: Directory containing JDA90.csv, JDA91.csv, JDA92.csv.

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed.
    """
    csv_dir = Path(csv_dir)
    jda_files = sorted(csv_dir.glob("JDA*.csv"))
    if not jda_files:
        msg = f"No JDA*.csv files found in {csv_dir}"
        raise FileNotFoundError(msg)

    logger.info("Found %d JUDA CSV files: %s", len(jda_files), [f.name for f in jda_files])

    records: list[dict] = []
    for csv_file in jda_files:
        with csv_file.open(encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";", quotechar='"')
            for lineno, row in enumerate(reader, start=2):
                try:
                    record = JudaRecord.from_csv_row(row)
                except Exception as exc:
                    logger.warning("Skipping JUDA row %d in %s: %s", lineno, csv_file.name, exc)
                    continue
                flat = record.model_dump()
                flat["searchable_text"] = record.searchable_text
                records.append(flat)

    if not records:
        msg = f"No valid JUDA records parsed from {csv_dir}"
        raise ValueError(msg)

    logger.info("Parsed %d JUDA records", len(records))

    table = db.create_table(JUDA_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_ritningar(
    db: lancedb.DBConnection,
    fira_path: str | Path,
    sira_dir: str | Path,
    *,
    dkod_path: str | Path | None = None,
    sakg_path: str | Path | None = None,
) -> lancedb.table.Table:
    """Ingest FIRA and SIRA CSV files into a single LanceDB table with FTS index.

    FIRA has a header row; SIRA files have NO header row.
    Both share the same 18-column structure. Optionally enriches DKOD and SAKG
    codes with human-readable descriptions from lookup tables.

    Args:
        db: LanceDB database connection.
        fira_path: Path to FIRA.csv (semicolon-delimited, latin-1, with header).
        sira_dir: Directory containing SIRA_*.csv files (headerless).
        dkod_path: Optional path to DKOD lookup CSV (KOD;KODFOERKLARING).
        sakg_path: Optional path to SAKG lookup CSV (KOD;KODFOERKLARING).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed.
    """
    dkod_map: dict[str, str] = {}
    sakg_map: dict[str, str] = {}
    if dkod_path:
        dkod_map = _load_lookup(dkod_path)
        logger.info("Loaded %d DKOD lookup entries", len(dkod_map))
    if sakg_path:
        sakg_map = _load_lookup(sakg_path)
        logger.info("Loaded %d SAKG lookup entries", len(sakg_map))

    records: list[dict] = []

    # --- FIRA (with header) ---
    fira_path = Path(fira_path)
    logger.info("Reading FIRA from %s ...", fira_path)
    with fira_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for lineno, row in enumerate(reader, start=2):
            try:
                record = RitningRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping FIRA row %d: %s", lineno, exc)
                continue
            _enrich_and_append(record, records, dkod_map, sakg_map)

    logger.info("Parsed %d FIRA records", len(records))

    # --- SIRA (headerless) ---
    sira_dir = Path(sira_dir)
    sira_files = sorted(sira_dir.glob("SIRA*.csv"))
    logger.info("Found %d SIRA files: %s", len(sira_files), [f.name for f in sira_files])

    sira_count = 0
    for csv_file in sira_files:
        with csv_file.open(encoding="latin-1", newline="") as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            for lineno, values in enumerate(reader, start=1):
                if len(values) < len(RITNING_FIELDNAMES):
                    logger.warning("Skipping SIRA row %d in %s: only %d columns", lineno, csv_file.name, len(values))
                    continue
                try:
                    record = RitningRecord.from_csv_list(values)
                except Exception as exc:
                    logger.warning("Skipping SIRA row %d in %s: %s", lineno, csv_file.name, exc)
                    continue
                _enrich_and_append(record, records, dkod_map, sakg_map)
                sira_count += 1

    logger.info("Parsed %d SIRA records", sira_count)

    if not records:
        msg = f"No valid drawing records parsed from {fira_path} and {sira_dir}"
        raise ValueError(msg)

    logger.info("Total drawing records: %d", len(records))

    table = db.create_table(FIRA_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def _enrich_and_append(
    record: RitningRecord,
    records: list[dict],
    dkod_map: dict[str, str],
    sakg_map: dict[str, str],
) -> None:
    """Enrich a RitningRecord with lookup descriptions and append to records list."""
    flat = record.model_dump()

    # Enrich DKOD and SAKG with human-readable descriptions
    if dkod_map and record.dkod and record.dkod in dkod_map:
        flat["dkod"] = f"{record.dkod} ({dkod_map[record.dkod]})"
    if sakg_map and record.sakg and record.sakg in sakg_map:
        flat["sakg"] = f"{record.sakg} ({sakg_map[record.sakg]})"

    flat["searchable_text"] = record.searchable_text
    records.append(flat)
