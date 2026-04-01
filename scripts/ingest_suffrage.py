"""Download and ingest women's suffrage CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_suffrage.py [--rostratt-dir PATH] [--fkpr PATH] [--output PATH]

By default, downloads from upstream and ingests both tables.
Use --rostratt-dir / --fkpr to provide local files instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_suffrage_lib.ingest import ingest_fkpr, ingest_rostratt


DEFAULT_OUTPUT = Path("data/suffrage")
ROSTRATT_ZIP_URL = "https://filer.riksarkivet.se/registerdata/R%C3%B6str%C3%A4tt/csv.zip"
FKPR_CSV_URL = "https://filer.riksarkivet.se/registerdata/FKPR/csv/GBG_FKPR.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_and_extract_rostratt(dest_dir: Path) -> Path:
    """Download Rösträtt CSV zip and extract county files."""
    zip_path = dest_dir / "rostratt.zip"
    logger.info("Downloading Rösträtt CSV zip from %s ...", ROSTRATT_ZIP_URL)
    with urlopen(ROSTRATT_ZIP_URL) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    csv_dir = dest_dir / "rostratt"
    csv_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(csv_dir)

    # Find the directory containing the CSV files
    csv_files = list(csv_dir.rglob("*.csv"))
    if csv_files:
        # Use the parent of the first CSV found
        return csv_files[0].parent
    return csv_dir


def download_fkpr(dest_dir: Path) -> Path:
    """Download FKPR CSV from Riksarkivet."""
    csv_path = dest_dir / "GBG_FKPR.csv"
    logger.info("Downloading FKPR from %s ...", FKPR_CSV_URL)
    with urlopen(FKPR_CSV_URL) as resp:
        csv_path.write_bytes(resp.read())
    logger.info("Saved FKPR CSV to %s (%d bytes)", csv_path, csv_path.stat().st_size)
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest suffrage data into LanceDB")
    parser.add_argument("--rostratt-dir", type=Path, default=None, help="Local directory with Rösträtt county CSVs (skips download)")
    parser.add_argument("--fkpr", type=Path, default=None, help="Local FKPR CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/suffrage)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Rösträtt
        rostratt_dir = args.rostratt_dir
        if rostratt_dir is None:
            rostratt_dir = download_and_extract_rostratt(tmp_path)
        print(f"Ingesting Rösträtt from {rostratt_dir} ...")
        rostratt_table = ingest_rostratt(db, rostratt_dir)
        print(f"  \u2192 {rostratt_table.count_rows()} rows")

        # FKPR
        fkpr_path = args.fkpr
        if fkpr_path is None:
            fkpr_path = download_fkpr(tmp_path)
        print(f"Ingesting FKPR from {fkpr_path} ...")
        fkpr_table = ingest_fkpr(db, fkpr_path)
        print(f"  \u2192 {fkpr_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
