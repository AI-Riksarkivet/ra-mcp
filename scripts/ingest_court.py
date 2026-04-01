"""Download and ingest court records CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_court.py [--output PATH]

Downloads both Domboksregister and Medelstad CSV zips from upstream,
extracts, joins related tables, and ingests into LanceDB.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_court_lib.ingest import ingest_domboksregister, ingest_medelstad


DEFAULT_OUTPUT = Path("data/court")

DOMBOKSREGISTER_ZIP_URL = "https://filer.riksarkivet.se/registerdata/Domboksregister/csv/Csv.zip"
MEDELSTAD_ZIP_URL = "https://filer.riksarkivet.se/registerdata/medelstad/medelstad_csv.zip"

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
    # Prefer exact match
    for c in candidates:
        if c.name.lower() == name.lower():
            return c
    if candidates:
        return candidates[0]
    msg = f"Could not find {name} under {base}"
    raise FileNotFoundError(msg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest court records into LanceDB")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/court)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- Domboksregister ---
        domboks_dir = tmp_path / "domboksregister"
        domboks_dir.mkdir()
        extracted = _download_and_extract(DOMBOKSREGISTER_ZIP_URL, domboks_dir)
        person_csv = _find_csv(extracted, "Person.csv")
        paragraf_csv = _find_csv(extracted, "Paragraf.csv")

        print(f"Ingesting Domboksregister from {person_csv} + {paragraf_csv} ...")
        domboks_table = ingest_domboksregister(db, person_csv, paragraf_csv)
        print(f"  -> {domboks_table.count_rows()} rows")

        # --- Medelstad ---
        medelstad_dir = tmp_path / "medelstad"
        medelstad_dir.mkdir()
        extracted = _download_and_extract(MEDELSTAD_ZIP_URL, medelstad_dir)
        personposter_csv = _find_csv(extracted, "personposter.csv")
        maal_csv = _find_csv(extracted, "maal.csv")

        print(f"Ingesting Medelstad from {personposter_csv} + {maal_csv} ...")
        medelstad_table = ingest_medelstad(db, personposter_csv, maal_csv)
        print(f"  -> {medelstad_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
