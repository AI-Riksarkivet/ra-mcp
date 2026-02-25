"""Shared fixtures for xml package tests."""

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


@pytest.fixture()
def alto_word_level_xml() -> str:
    """ALTO v4 with multiple <String> per TextLine, no WC attribute."""
    return (FIXTURES / "30002056_00010.xml").read_text()


@pytest.fixture()
def alto_line_level_xml() -> str:
    """ALTO v4 with single <String> per TextLine, WC on String."""
    return (FIXTURES / "451511_1512_01_alto.xml").read_text()


@pytest.fixture()
def page_xml() -> str:
    """PAGE XML with <TextEquiv><Unicode>, conf on TextEquiv."""
    return (FIXTURES / "451511_1512_01_page.xml").read_text()


@pytest.fixture()
def alto_transkribus_xml() -> str:
    """ALTO v4 from Transkribus: no Shape/Polygon on TextLines, BASELINE attribute."""
    return (FIXTURES / "R0001203_00010.xml").read_text()
