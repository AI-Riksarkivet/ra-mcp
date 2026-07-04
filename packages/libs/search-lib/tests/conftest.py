"""Shared fixtures for search package tests."""

import json
from pathlib import Path

import pytest


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def search_response_json() -> dict:
    """Parsed search API response with 2 records and snippets."""
    return json.loads((FIXTURES / "search_response.json").read_text())
