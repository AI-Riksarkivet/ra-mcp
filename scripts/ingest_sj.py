"""Download and ingest SJ railway records CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_sj.py [--output PATH]

Downloads JUDA, FIRA, and SIRA CSV zips from Riksarkivet, extracts,
optionally enriches lookup codes, and ingests into LanceDB.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_sj_lib.ingest import ingest_juda, ingest_ritningar


DEFAULT_OUTPUT = Path("data/sj")

JUDA_ZIP_URL = "https://filer.riksarkivet.se/registerdata/SJjordregister/csv/JUDA.zip"
FIRA_ZIP_URL = "https://filer.riksarkivet.se/registerdata/SJritningar/csv/FIRA.zip"
SIRA_ZIP_URL = "https://filer.riksarkivet.se/registerdata/SJritningar/csv/SIRA.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _download_and_extract(url: str, dest_dir: Path) -> Path:
    """Download a zip from URL and extract to dest_dir. Return extraction path."""
    zip_path = dest_dir / "download.zip"
    logger.info("Downloading %s ...", url)
    with urlopen(url) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    extract_dir = dest_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    return extract_dir


def _find_csv(base: Path, name: str) -> Path:
    """Find a CSV file by name (case-insensitive) under base directory."""
    candidates = list(base.rglob(f"*{name}*"))
    for c in candidates:
        if c.name.lower() == name.lower():
            return c
    if candidates:
        return candidates[0]
    msg = f"Could not find {name} under {base}"
    raise FileNotFoundError(msg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest SJ railway records into LanceDB")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/sj)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- JUDA ---
        juda_dir = tmp_path / "juda"
        juda_dir.mkdir()
        extracted = _download_and_extract(JUDA_ZIP_URL, juda_dir)
        # Find the directory containing JDA*.csv files
        jda_files = list(extracted.rglob("JDA*.csv"))
        if not jda_files:
            print("Error: No JDA*.csv files found in JUDA zip")
            return
        csv_dir = jda_files[0].parent

        print(f"Ingesting JUDA from {csv_dir} ...")
        juda_table = ingest_juda(db, csv_dir)
        print(f"  -> {juda_table.count_rows()} rows")

        # --- FIRA ---
        fira_dir = tmp_path / "fira"
        fira_dir.mkdir()
        extracted_fira = _download_and_extract(FIRA_ZIP_URL, fira_dir)
        fira_csv = _find_csv(extracted_fira, "FIRA.csv")

        # Try to find lookup tables
        dkod_path = None
        sakg_path = None
        try:
            dkod_path = _find_csv(extracted_fira, "FIRA_DKOD.csv")
            print(f"Found DKOD lookup: {dkod_path}")
        except FileNotFoundError:
            pass
        try:
            sakg_path = _find_csv(extracted_fira, "SAKG.csv")
            print(f"Found SAKG lookup: {sakg_path}")
        except FileNotFoundError:
            pass

        # --- SIRA ---
        sira_dir = tmp_path / "sira"
        sira_dir.mkdir()
        extracted_sira = _download_and_extract(SIRA_ZIP_URL, sira_dir)
        # SIRA files are headerless; find directory with SIRA_*.csv
        sira_files = list(extracted_sira.rglob("SIRA*.csv"))
        if not sira_files:
            print("Warning: No SIRA*.csv files found in SIRA zip")
            sira_csv_dir = extracted_sira
        else:
            sira_csv_dir = sira_files[0].parent
            # Also check for lookup tables in SIRA zip
            if dkod_path is None:
                try:
                    dkod_path = _find_csv(extracted_sira, "DKOD.csv")
                    print(f"Found DKOD lookup in SIRA: {dkod_path}")
                except FileNotFoundError:
                    pass
            if sakg_path is None:
                try:
                    sakg_path = _find_csv(extracted_sira, "SAKG.csv")
                    print(f"Found SAKG lookup in SIRA: {sakg_path}")
                except FileNotFoundError:
                    pass

        print(f"Ingesting drawings from {fira_csv} + {sira_csv_dir} ...")
        ritningar_table = ingest_ritningar(db, fira_csv, sira_csv_dir, dkod_path=dkod_path, sakg_path=sakg_path)
        print(f"  -> {ritningar_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
