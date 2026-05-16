"""Shared fixtures for pdf-mcp tests."""

import pytest

import ra_mcp_pdf_mcp.state as _state_mod
import ra_mcp_pdf_mcp.cache as _cache_mod


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level state between tests."""
    _state_mod.latest_view_id = ""
    _cache_mod.pdf_cache.clear()
    _cache_mod.blocks_cache.clear()
    yield
    _state_mod.latest_view_id = ""
    _cache_mod.pdf_cache.clear()
    _cache_mod.blocks_cache.clear()


@pytest.fixture()
def sample_pages() -> list[dict]:
    """Structured JSON pages mimicking the DataLab format."""
    return [
        {
            "page": 0,
            "bbox": [0, 0, 595, 842],
            "children": [
                {
                    "html": "<p>Kungliga Majestäts kansli</p>",
                    "bbox": [72, 100, 400, 130],
                    "block_type": "SectionHeader",
                },
                {
                    "html": "<p>Stockholm den 15 mars 1723</p>",
                    "bbox": [72, 140, 400, 160],
                    "block_type": "Text",
                },
                {
                    "html": "<p>Trolldomsprocessen i Norrland</p>",
                    "bbox": [72, 170, 400, 190],
                    "block_type": "Text",
                },
            ],
        },
        {
            "page": 1,
            "bbox": [0, 0, 595, 842],
            "children": [
                {
                    "html": "<p>Domstolens <b>beslut</b> i målet</p>",
                    "bbox": [72, 100, 400, 130],
                    "block_type": "Text",
                },
                {
                    "html": "",
                    "bbox": [72, 140, 400, 160],
                    "block_type": "Figure",
                },
            ],
        },
        {
            "page": 2,
            "bbox": [0, 0, 595, 842],
            "children": [
                {
                    "html": "<p>Stockholm Stockholm Stockholm</p>",
                    "bbox": [72, 100, 400, 130],
                    "block_type": "Text",
                },
            ],
        },
    ]
