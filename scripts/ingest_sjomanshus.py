"""Download and ingest Sjömanshus CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_sjomanshus.py [--liggare PATH] [--matrikel PATH] [--output PATH]

By default, downloads the CSV zip from upstream and ingests both tables.
Use --liggare / --matrikel to provide local files instead.
"""

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_sjomanshus_lib.ingest import ingest_liggare, ingest_matrikel


DEFAULT_OUTPUT = Path("data/sjomanshus")
CSV_ZIP_URL = "https://filer.riksarkivet.se/registerdata/Sj%C3%B6manshus/csv/csv.zip"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_and_extract(dest_dir: Path) -> tuple[Path, Path]:
    """Download Sjömanshus CSV zip and extract Liggare.csv and Matrikel.csv."""
    zip_path = dest_dir / "csv.zip"
    logger.info("Downloading Sjömanshus CSV zip from %s ...", CSV_ZIP_URL)
    with urlopen(CSV_ZIP_URL) as resp:
        zip_path.write_bytes(resp.read())
    logger.info("Saved zip to %s (%d bytes)", zip_path, zip_path.stat().st_size)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)

    liggare_path = dest_dir / "Liggare.csv"
    matrikel_path = dest_dir / "Matrikel.csv"

    if not liggare_path.exists():
        # Try to find the files in subdirectories
        candidates = list(dest_dir.rglob("Liggare.csv"))
        if candidates:
            liggare_path = candidates[0]
    if not matrikel_path.exists():
        candidates = list(dest_dir.rglob("Matrikel.csv"))
        if candidates:
            matrikel_path = candidates[0]

    return liggare_path, matrikel_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest Sjömanshus into LanceDB")
    parser.add_argument("--liggare", type=Path, default=None, help="Local Liggare CSV path (skips download)")
    parser.add_argument("--matrikel", type=Path, default=None, help="Local Matrikel CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: data/sjomanshus)")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        liggare_path = args.liggare
        matrikel_path = args.matrikel

        if liggare_path is None or matrikel_path is None:
            dl_liggare, dl_matrikel = download_and_extract(tmp_path)
            if liggare_path is None:
                liggare_path = dl_liggare
            if matrikel_path is None:
                matrikel_path = dl_matrikel

        # Ingest Liggare
        print(f"Ingesting Liggare from {liggare_path} ...")
        liggare_table = ingest_liggare(db, liggare_path)
        print(f"  → {liggare_table.count_rows()} rows")

        # Ingest Matrikel
        print(f"Ingesting Matrikel from {matrikel_path} ...")
        matrikel_table = ingest_matrikel(db, matrikel_path)
        print(f"  → {matrikel_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
