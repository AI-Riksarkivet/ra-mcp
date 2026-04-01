"""Download and ingest Specialsök CSV datasets into LanceDB tables.

Usage:
    uv run python scripts/ingest_specialsok.py [--output PATH]

Downloads all 5 Specialsök datasets from Riksarkivet and ingests into LanceDB.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_specialsok_lib.ingest import (
    ingest_fangrullor,
    ingest_flygvapen,
    ingest_kurhuset,
    ingest_press,
    ingest_video,
)


DEFAULT_OUTPUT = Path("data/specialsok")

# Dataset URLs from Riksarkivet Specialsök
FLYGVAPEN_URL = "https://filer.riksarkivet.se/registerdata/Flygvapnet/csv/Csv.zip"
FANGRULLOR_URL = "https://filer.riksarkivet.se/registerdata/Fangrullor/csv/Csv.zip"
KURHUSET_URL = "https://filer.riksarkivet.se/registerdata/Kurhuset/csv/Csv.zip"
PRESS_URL = "https://filer.riksarkivet.se/registerdata/Presskonferenser/csv/Csv.zip"
VIDEO_URL = "https://filer.riksarkivet.se/registerdata/Videobutiker/csv/Csv.zip"

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


def _find_csv(base: Path, pattern: str = "*.csv") -> Path:
    """Find a CSV file under base directory."""
    candidates = list(base.rglob(pattern))
    if not candidates:
        msg = f"Could not find {pattern} under {base}"
        raise FileNotFoundError(msg)
    # Prefer largest file (the main data file)
    return max(candidates, key=lambda p: p.stat().st_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Specialsök datasets into LanceDB")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/specialsok)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    datasets = [
        ("Flygvapenhaverier", FLYGVAPEN_URL, ingest_flygvapen),
        ("Fångrullor", FANGRULLOR_URL, ingest_fangrullor),
        ("Kurhuset", KURHUSET_URL, ingest_kurhuset),
        ("Presskonferenser", PRESS_URL, ingest_press),
        ("Videobutiker", VIDEO_URL, ingest_video),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        for name, url, ingest_fn in datasets:
            dataset_dir = tmp_path / name.lower()
            dataset_dir.mkdir()
            try:
                extracted = _download_and_extract(url, dataset_dir)
                csv_file = _find_csv(extracted)
                print(f"Ingesting {name} from {csv_file} ...")
                table = ingest_fn(db, csv_file)
                print(f"  -> {table.count_rows()} rows")
            except Exception as exc:
                print(f"  ERROR ingesting {name}: {exc}")
                logger.error("Failed to ingest %s: %s", name, exc, exc_info=True)

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
