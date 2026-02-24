"""Shared fixtures for oai-pmh package tests."""

from pathlib import Path

import pytest


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def oai_pmh_xml() -> bytes:
    """OAI-PMH GetRecord response with EAD metadata."""
    return (FIXTURES / "oai_pmh_response.xml").read_bytes()
