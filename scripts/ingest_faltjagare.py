"""Download and ingest Fältjägare CSV data into a LanceDB table.

Usage:
    uv run python scripts/ingest_faltjagare.py [--csv PATH] [--output PATH]

By default, downloads the CSV from upstream and ingests it.
Use --csv to provide a local file instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_faltjagare_lib.ingest import ingest_faltjagare


DEFAULT_OUTPUT = Path("data/faltjagare")
FALTJAGARE_ZIP_URL = "https://filer.riksarkivet.se/registerdata/f%C3%A4ltj%C3%A4gare/faeltjaegare_csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_faltjagare(dest_dir: Path) -> Path:
    """Download and extract FAELJAEGARE.csv from Riksarkivet."""
    zip_path = dest_dir / "faeltjaegare_csv.zip"
    logger.info("Downloading Fältjägare from %s ...", FALTJAGARE_ZIP_URL)
    with urlopen(FALTJAGARE_ZIP_URL) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist() if n.upper().endswith(".CSV")]
        if not csv_names:
            raise FileNotFoundError(f"No CSV found in {zip_path}. Contents: {zf.namelist()}")
        csv_name = csv_names[0]
        zf.extract(csv_name, dest_dir)
        extracted = dest_dir / csv_name
        logger.info("Extracted %s (%d bytes)", extracted, extracted.stat().st_size)
        return extracted


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Fältjägare into LanceDB")
    parser.add_argument("--csv", type=Path, default=None, help="Local FAELJAEGARE CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/faltjagare)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        csv_path = args.csv
        if csv_path is None:
            csv_path = download_faltjagare(tmp_path)
        print(f"Ingesting Fältjägare from {csv_path} ...")
        table = ingest_faltjagare(db, csv_path)
        print(f"  \u2192 {table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
