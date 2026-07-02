"""Shared fixtures for iiif package tests."""

from pathlib import Path

import pytest


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def iiif_collection_json() -> str:
    """IIIF v3 Collection with 2 manifests."""
    return (FIXTURES / "iiif_collection.json").read_text()
