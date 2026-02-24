"""Shared fixtures for alto package tests."""

from pathlib import Path

import pytest


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def alto_sample_xml() -> bytes:
    """Minimal ALTO v4 XML with a few String elements."""
    return (FIXTURES / "alto_sample.xml").read_bytes()


@pytest.fixture()
def alto_blank_xml() -> bytes:
    """ALTO XML with no String elements (blank page)."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Layout>
    <Page WIDTH="2000" HEIGHT="3000">
      <PrintSpace>
      </PrintSpace>
    </Page>
  </Layout>
</alto>"""
