"""Tests for ra_mcp_pdf_mcp.gallery."""

from ra_mcp_pdf_mcp.gallery import GALLERY_ITEMS, get_gallery_items


def test_get_gallery_items_returns_list():
    items = get_gallery_items()
    assert isinstance(items, list)
    assert len(items) > 0


def test_gallery_items_have_required_keys():
    for item in GALLERY_ITEMS:
        assert "url" in item
        assert "title" in item
        assert "description" in item
        assert "thumbnail_url" in item
        assert "category" in item


def test_gallery_urls_are_pdf_links():
    for item in GALLERY_ITEMS:
        assert ".pdf" in item["url"]
        assert item["url"].startswith("https://")


def test_get_gallery_items_returns_same_reference():
    assert get_gallery_items() is GALLERY_ITEMS
