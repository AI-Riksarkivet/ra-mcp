"""Ingest SDHK and MPO CSV data into LanceDB tables.

Usage:
    uv run python scripts/ingest_diplomatics.py /path/to/sdhk.csv /path/to/mpo.csv
"""

import sys
import logging
from pathlib import Path

import lancedb

from ra_mcp_diplomatics_lib.config import LANCEDB_PATH
from ra_mcp_diplomatics_lib.ingest import ingest_sdhk, ingest_mpo


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <sdhk.csv> <mpo.csv>")
        sys.exit(1)

    sdhk_path = Path(sys.argv[1])
    mpo_path = Path(sys.argv[2])

    if not sdhk_path.exists():
        print(f"SDHK file not found: {sdhk_path}")
        sys.exit(1)
    if not mpo_path.exists():
        print(f"MPO file not found: {mpo_path}")
        sys.exit(1)

    LANCEDB_PATH.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(LANCEDB_PATH)

    print(f"Ingesting SDHK from {sdhk_path}...")
    sdhk_table = ingest_sdhk(db, sdhk_path)
    print(f"  → {sdhk_table.count_rows()} rows")

    print(f"Ingesting MPO from {mpo_path}...")
    mpo_table = ingest_mpo(db, mpo_path)
    print(f"  → {mpo_table.count_rows()} rows")

    print(f"\nDone! Tables at: {LANCEDB_PATH}")


if __name__ == "__main__":
    main()
