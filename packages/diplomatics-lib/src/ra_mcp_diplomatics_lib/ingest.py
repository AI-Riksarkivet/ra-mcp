"""CSV ingest functions for SDHK and MPO records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import MPO_TABLE, SDHK_TABLE
from .models import MPORecord, SDHKRecord

if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def _load_id_set(path: str | Path | None) -> set[int]:
    """Load a set of integer IDs from a text file (one per line)."""
    if path is None:
        return set()
    path = Path(path)
    if not path.exists():
        return set()
    ids = set()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ids.add(int(line))
                except ValueError:
                    pass
    return ids


def ingest_sdhk(
    db: "lancedb.DBConnection",
    csv_path: str | Path,
    manifest_ids_path: str | Path | None = None,
    no_transcription_ids_path: str | Path | None = None,
) -> "lancedb.table.Table":
    """Ingest SDHK CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the SDHK CSV file (semicolon-delimited, latin-1 encoded).
        manifest_ids_path: Path to file listing SDHK IDs that have IIIF manifests.
        no_transcription_ids_path: Path to file listing SDHK IDs with manifests but no transcription.

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from the CSV.
    """
    csv_path = Path(csv_path)
    manifest_ids = _load_id_set(manifest_ids_path)
    no_transcription_ids = _load_id_set(no_transcription_ids_path)
    records: list[dict] = []

    with csv_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for lineno, row in enumerate(reader, start=2):
            try:
                record = SDHKRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping SDHK row %d: %s", lineno, exc)
                continue
            if manifest_ids:
                record.has_manifest = record.id in manifest_ids
                record.has_transcription = record.has_manifest and record.id not in no_transcription_ids
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            flat["manifest_url"] = record.manifest_url
            records.append(flat)

    if not records:
        raise ValueError(f"No valid SDHK records parsed from {csv_path}")

    logger.info("Parsed %d SDHK records", len(records))

    table = db.create_table(SDHK_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table


def ingest_mpo(db: "lancedb.DBConnection", csv_path: str | Path) -> "lancedb.table.Table":
    """Ingest MPO CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the MPO CSV file (comma-delimited, UTF-8 encoded).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from the CSV.
    """
    csv_path = Path(csv_path)
    records: list[dict] = []

    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            try:
                record = MPORecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping MPO row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            flat["manifest_url"] = record.manifest_url
            records.append(flat)

    if not records:
        raise ValueError(f"No valid MPO records parsed from {csv_path}")

    logger.info("Parsed %d MPO records", len(records))

    table = db.create_table(MPO_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
