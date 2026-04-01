"""Download and ingest Wincars vehicle registration CSV data into LanceDB.

Usage:
    uv run python scripts/ingest_wincars.py [--csv-dir PATH] [--output PATH]

By default, downloads from upstream and ingests all county files.
Use --csv-dir to provide a local directory instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_wincars_lib.ingest import ingest_wincars


DEFAULT_OUTPUT = Path("data/wincars")

WINCARS_ZIP_URL = "https://filer.riksarkivet.se/registerdata/wincars/wincars_csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_and_extract_zip(url: str, dest_dir: Path) -> Path:
    """Download a zip file and extract CSV files, returning the directory containing them."""
    zip_path = dest_dir / "wincars.zip"
    logger.info("Downloading Wincars CSV zip from %s ...", url)
    with urlopen(url) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    csv_dir = dest_dir / "wincars"
    csv_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(csv_dir)

    # Find the directory containing the CSV files
    csv_files = list(csv_dir.rglob("*.csv"))
    if csv_files:
        return csv_files[0].parent
    return csv_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Wincars vehicle records into LanceDB")
    parser.add_argument("--csv-dir", type=Path, default=None, help="Local directory with Wincars county CSVs (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/wincars)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        csv_dir = args.csv_dir
        if csv_dir is None:
            csv_dir = download_and_extract_zip(WINCARS_ZIP_URL, tmp_path)

        print(f"Ingesting Wincars from {csv_dir} ...")
        table = ingest_wincars(db, csv_dir)
        print(f"  \u2192 {table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
