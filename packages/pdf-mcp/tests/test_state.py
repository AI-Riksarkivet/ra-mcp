"""Tests for ra_mcp_pdf_mcp.state."""

import pytest

from ra_mcp_pdf_mcp.models import PdfViewerState
from ra_mcp_pdf_mcp.state import get_active_state, get_state, put_state
import ra_mcp_pdf_mcp.state as _state_mod


async def test_get_state_returns_default_for_unknown_id():
    state = await get_state("nonexistent-id")
    assert state.view_id == "nonexistent-id"
    assert state.version == 0


async def test_put_state_increments_version():
    state = PdfViewerState(view_id="test-1", url="https://example.com/a.pdf")
    result = await put_state(state)
    assert result["version"] == 1

    state2 = await get_state("test-1")
    result2 = await put_state(state2)
    assert result2["version"] == 2


async def test_put_state_sets_latest_view_id():
    state = PdfViewerState(view_id="view-abc", url="https://example.com/b.pdf")
    await put_state(state)
    assert _state_mod.latest_view_id == "view-abc"


async def test_get_active_state_raises_when_no_viewer():
    with pytest.raises(LookupError, match="No PDF viewer is open"):
        await get_active_state()


async def test_get_active_state_returns_latest():
    state = PdfViewerState(view_id="active-1", url="https://example.com/c.pdf", title="Doc C")
    await put_state(state)

    active = await get_active_state()
    assert active.view_id == "active-1"
    assert active.title == "Doc C"
    assert active.version == 1


async def test_put_state_returns_dict_for_structured_content():
    state = PdfViewerState(view_id="dict-test", url="https://example.com/d.pdf")
    result = await put_state(state)
    assert isinstance(result, dict)
    assert result["view_id"] == "dict-test"
    assert result["url"] == "https://example.com/d.pdf"


async def test_multiple_views_are_independent():
    state_a = PdfViewerState(view_id="view-a", url="https://a.pdf", title="A")
    state_b = PdfViewerState(view_id="view-b", url="https://b.pdf", title="B")
    await put_state(state_a)
    await put_state(state_b)

    retrieved_a = await get_state("view-a")
    retrieved_b = await get_state("view-b")
    assert retrieved_a.title == "A"
    assert retrieved_b.title == "B"
    assert _state_mod.latest_view_id == "view-b"
