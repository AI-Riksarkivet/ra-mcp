"""Download and ingest Aktiebolag CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_aktiebolag.py [--output PATH]

Downloads the CSV zip from upstream, extracts AKTIEBOLAG.txt and
STYRELSEMEDLEMMAR.txt, joins them, and ingests into LanceDB.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_aktiebolag_lib.ingest import ingest_aktiebolag


DEFAULT_OUTPUT = Path("data/aktiebolag")
AKTIEBOLAG_ZIP_URL = "https://filer.riksarkivet.se/registerdata/aktiebolag/aktiebolag_csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _download_and_extract(dest_dir: Path) -> Path:
    """Download and extract the Aktiebolag zip. Return extraction directory."""
    zip_path = dest_dir / "aktiebolag_csv.zip"
    logger.info("Downloading Aktiebolag from %s ...", AKTIEBOLAG_ZIP_URL)
    with urlopen(AKTIEBOLAG_ZIP_URL) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    extract_dir = dest_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    return extract_dir


def _find_file(base: Path, name: str) -> Path:
    """Find a file by name (case-insensitive) under base directory."""
    candidates = list(base.rglob(f"*{name}*"))
    for c in candidates:
        if c.name.upper() == name.upper():
            return c
    if candidates:
        return candidates[0]
    msg = f"Could not find {name} under {base}"
    raise FileNotFoundError(msg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Aktiebolag into LanceDB")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/aktiebolag)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        extracted = _download_and_extract(tmp_path)

        bolag_path = _find_file(extracted, "AKTIEBOLAG.txt")
        styrelse_path = _find_file(extracted, "STYRELSEMEDLEMMAR.txt")

        print(f"Ingesting Aktiebolag from {bolag_path} + {styrelse_path} ...")
        bolag_table, styrelse_table = ingest_aktiebolag(db, bolag_path, styrelse_path)
        print(f"  -> bolag: {bolag_table.count_rows()} rows")
        print(f"  -> styrelse: {styrelse_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
