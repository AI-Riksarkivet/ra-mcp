"""Download and ingest Filmcensur CSV data into a LanceDB table.

Usage:
    uv run python scripts/ingest_filmcensur.py [--filmreg PATH] [--output PATH]

By default, downloads the CSV from upstream and ingests it.
Use --filmreg to provide a local file instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_filmcensur_lib.ingest import ingest_filmreg


DEFAULT_OUTPUT = Path("data/filmcensur")
FILMREG_ZIP_URL = "https://filer.riksarkivet.se/registerdata/filmcensur/filmregistret_csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_filmreg(dest_dir: Path) -> Path:
    """Download and extract FILMREG.csv from Riksarkivet."""
    zip_path = dest_dir / "filmregistret_csv.zip"
    logger.info("Downloading Filmreg from %s ...", FILMREG_ZIP_URL)
    with urlopen(FILMREG_ZIP_URL) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    with zipfile.ZipFile(zip_path) as zf:
        # Find FILMREG.csv in the archive
        csv_names = [n for n in zf.namelist() if n.upper().endswith("FILMREG.CSV")]
        if not csv_names:
            raise FileNotFoundError(f"No FILMREG.csv found in {zip_path}. Contents: {zf.namelist()}")
        csv_name = csv_names[0]
        zf.extract(csv_name, dest_dir)
        extracted = dest_dir / csv_name
        logger.info("Extracted %s (%d bytes)", extracted, extracted.stat().st_size)
        return extracted


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Filmcensur into LanceDB")
    parser.add_argument("--filmreg", type=Path, default=None, help="Local FILMREG CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/filmcensur)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Filmreg
        filmreg_path = args.filmreg
        if filmreg_path is None:
            filmreg_path = download_filmreg(tmp_path)
        print(f"Ingesting Filmreg from {filmreg_path} ...")
        filmreg_table = ingest_filmreg(db, filmreg_path)
        print(f"  \u2192 {filmreg_table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
