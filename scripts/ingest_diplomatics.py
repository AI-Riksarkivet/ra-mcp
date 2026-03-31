"""Download and ingest SDHK and MPO CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_diplomatics.py [--download] [--sdhk PATH] [--mpo PATH]

By default, downloads CSVs from upstream sources and ingests them.
Use --sdhk/--mpo to provide local files instead.
"""

import argparse
import io
import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_diplomatics_lib.config import LANCEDB_PATH
from ra_mcp_diplomatics_lib.ingest import ingest_mpo, ingest_sdhk

SDHK_CSV_URL = "https://filer.riksarkivet.se/registerdata/SDHK/csv/sdhk_2411.csv"
MPO_ZIP_URL = "https://zenodo.org/api/records/17287665/files-archive"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_sdhk(dest: Path) -> Path:
    """Download SDHK CSV from Riksarkivet."""
    logger.info("Downloading SDHK from %s ...", SDHK_CSV_URL)
    with urlopen(SDHK_CSV_URL) as resp:
        dest.write_bytes(resp.read())
    logger.info("Saved SDHK CSV to %s (%d bytes)", dest, dest.stat().st_size)
    return dest


def download_mpo(dest: Path) -> Path:
    """Download MPO CSV from Zenodo (zip archive containing mpo.csv)."""
    logger.info("Downloading MPO from %s ...", MPO_ZIP_URL)
    with urlopen(MPO_ZIP_URL) as resp:
        zip_bytes = resp.read()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
        dest.write_bytes(zf.read(csv_name))
    logger.info("Extracted %s to %s (%d bytes)", csv_name, dest, dest.stat().st_size)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest SDHK/MPO into LanceDB")
    parser.add_argument("--sdhk", type=Path, default=None, help="Local SDHK CSV path (skips download)")
    parser.add_argument("--mpo", type=Path, default=None, help="Local MPO CSV path (skips download)")
    parser.add_argument("--manifest-ids", type=Path, default=None, help="File listing SDHK IDs with IIIF manifests")
    parser.add_argument("--no-transcription-ids", type=Path, default=None, help="File listing SDHK IDs without transcription")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path (default: from config)")
    args = parser.parse_args()

    output_path = args.output or LANCEDB_PATH
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # SDHK
        sdhk_path = args.sdhk
        if sdhk_path is None:
            sdhk_path = tmp_path / "sdhk.csv"
            download_sdhk(sdhk_path)
        print(f"Ingesting SDHK from {sdhk_path} ...")
        sdhk_table = ingest_sdhk(
            db, sdhk_path,
            manifest_ids_path=args.manifest_ids,
            no_transcription_ids_path=args.no_transcription_ids,
        )
        print(f"  → {sdhk_table.count_rows()} rows")

        # MPO
        mpo_path = args.mpo
        if mpo_path is None:
            mpo_path = tmp_path / "mpo.csv"
            download_mpo(mpo_path)
        print(f"Ingesting MPO from {mpo_path} ...")
        mpo_table = ingest_mpo(db, mpo_path)
        print(f"  → {mpo_table.count_rows()} rows")

    print(f"\nDone! Tables at: {output_path}")


if __name__ == "__main__":
    main()
