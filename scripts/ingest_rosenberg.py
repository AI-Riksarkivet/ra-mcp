"""Download and ingest Rosenberg CSV data into a LanceDB table.

Usage:
    uv run python scripts/ingest_rosenberg.py [--csv PATH] [--output PATH]

By default, downloads the CSV from upstream and ingests it.
Use --csv to provide a local file instead.
"""

import argparse
import logging
import tempfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_rosenberg_lib.ingest import ingest_rosenberg


DEFAULT_OUTPUT = Path("data/rosenberg")
ROSENBERG_CSV_URL = "https://filer.riksarkivet.se/registerdata/Rosenberg/Rosenberg_bearbetad/csv/Rosenberg_bearbetad.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_rosenberg(dest_dir: Path) -> Path:
    """Download Rosenberg_bearbetad.csv from Riksarkivet."""
    csv_path = dest_dir / "Rosenberg_bearbetad.csv"
    logger.info("Downloading Rosenberg from %s ...", ROSENBERG_CSV_URL)
    with urlopen(ROSENBERG_CSV_URL) as resp:
        csv_path.write_bytes(resp.read())
    logger.info("Saved CSV to %s (%d bytes)", csv_path, csv_path.stat().st_size)
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Rosenberg into LanceDB")
    parser.add_argument("--csv", type=Path, default=None, help="Local Rosenberg CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/rosenberg)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        csv_path = args.csv
        if csv_path is None:
            csv_path = download_rosenberg(tmp_path)
        print(f"Ingesting Rosenberg from {csv_path} ...")
        table = ingest_rosenberg(db, csv_path)
        print(f"  \u2192 {table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
