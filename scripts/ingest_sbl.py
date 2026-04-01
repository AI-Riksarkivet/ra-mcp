"""Download and ingest SBL CSV data into a LanceDB table.

Usage:
    uv run python scripts/ingest_sbl.py [--sbl PATH] [--output PATH]

By default, downloads the CSV from upstream and ingests it.
Use --sbl to provide a local file instead.
"""

import argparse
import logging
import tempfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_sbl_lib.ingest import ingest_sbl


DEFAULT_OUTPUT = Path("data/sbl")
SBL_CSV_URL = "https://filer.riksarkivet.se/registerdata/SBL/csv/SBL_2023.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_sbl(dest: Path) -> Path:
    """Download SBL CSV from Riksarkivet."""
    logger.info("Downloading SBL from %s ...", SBL_CSV_URL)
    with urlopen(SBL_CSV_URL) as resp:
        dest.write_bytes(resp.read())
    logger.info("Saved SBL CSV to %s (%d bytes)", dest, dest.stat().st_size)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest SBL into LanceDB")
    parser.add_argument("--sbl", type=Path, default=None, help="Local SBL CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/sbl)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # SBL
        sbl_path = args.sbl
        if sbl_path is None:
            sbl_path = tmp_path / "sbl.csv"
            download_sbl(sbl_path)
        print(f"Ingesting SBL from {sbl_path} ...")
        sbl_table = ingest_sbl(db, sbl_path)
        print(f"  → {sbl_table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
