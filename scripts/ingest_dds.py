"""Download and ingest DDS church records CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_dds.py [--fodelse-dir PATH] [--doda-dir PATH] [--vigsel-dir PATH] [--output PATH]

By default, downloads from upstream and ingests all three tables.
Use --fodelse-dir / --doda-dir / --vigsel-dir to provide local directories instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_dds_lib.ingest import ingest_doda, ingest_fodelse, ingest_vigsel


DEFAULT_OUTPUT = Path("data/dds")

FODELSE_ZIP_URL = "https://filer.riksarkivet.se/registerdata/DDS/Fodda/Fodelse_csv.zip"
DODA_ZIP_URL = "https://filer.riksarkivet.se/registerdata/DDS/Doda/Doda_csv.zip"
VIGSEL_ZIP_URL = "https://filer.riksarkivet.se/registerdata/DDS/Vigslar/Vigsel_csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_and_extract_zip(url: str, dest_dir: Path, label: str) -> Path:
    """Download a zip file and extract CSV files, returning the directory containing them."""
    zip_path = dest_dir / f"{label}.zip"
    logger.info("Downloading %s CSV zip from %s ...", label, url)
    with urlopen(url) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    csv_dir = dest_dir / label
    csv_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(csv_dir)

    # Find the directory containing the CSV files
    csv_files = list(csv_dir.rglob("*.csv"))
    if csv_files:
        return csv_files[0].parent
    return csv_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest DDS church records into LanceDB")
    parser.add_argument("--fodelse-dir", type=Path, default=None, help="Local directory with Födelse county CSVs (skips download)")
    parser.add_argument("--doda-dir", type=Path, default=None, help="Local directory with Döda county CSVs (skips download)")
    parser.add_argument("--vigsel-dir", type=Path, default=None, help="Local directory with Vigsel county CSVs (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/dds)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- Födelse table ---
        fodelse_dir = args.fodelse_dir
        if fodelse_dir is None:
            fodelse_dir = download_and_extract_zip(FODELSE_ZIP_URL, tmp_path, "fodelse")
        print(f"Ingesting F\u00f6delse from {fodelse_dir} ...")
        fodelse_table = ingest_fodelse(db, fodelse_dir)
        print(f"  \u2192 {fodelse_table.count_rows()} rows")

        # --- Döda table ---
        doda_dir = args.doda_dir
        if doda_dir is None:
            doda_dir = download_and_extract_zip(DODA_ZIP_URL, tmp_path, "doda")
        print(f"Ingesting D\u00f6da from {doda_dir} ...")
        doda_table = ingest_doda(db, doda_dir)
        print(f"  \u2192 {doda_table.count_rows()} rows")

        # --- Vigsel table ---
        vigsel_dir = args.vigsel_dir
        if vigsel_dir is None:
            vigsel_dir = download_and_extract_zip(VIGSEL_ZIP_URL, tmp_path, "vigsel")
        print(f"Ingesting Vigsel from {vigsel_dir} ...")
        vigsel_table = ingest_vigsel(db, vigsel_dir)
        print(f"  \u2192 {vigsel_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
