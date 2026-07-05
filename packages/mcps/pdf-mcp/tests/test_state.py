"""Tests for ra_mcp_pdf_mcp.state."""

import pytest

import ra_mcp_pdf_mcp.state as _state_mod
from ra_mcp_pdf_mcp.models import PdfViewerState
from ra_mcp_pdf_mcp.state import get_active_state, get_state, put_state


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
    # No request context in tests -> the "" (stdio/no-session) bucket.
    assert _state_mod._latest_view_by_session[""] == "view-abc"


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
    assert _state_mod._latest_view_by_session[""] == "view-b"


async def test_active_view_is_isolated_per_session(monkeypatch):
    # Two concurrent sessions must not share the "active view" pointer: session B opening
    # a viewer must not redirect session A's no-view_id mutation tools to B's document.
    current = {"session": "A"}
    monkeypatch.setattr(_state_mod, "_session_key", lambda: current["session"])

    current["session"] = "A"
    await put_state(PdfViewerState(view_id="view-A", url="https://a.pdf", title="A"))
    current["session"] = "B"
    await put_state(PdfViewerState(view_id="view-B", url="https://b.pdf", title="B"))

    current["session"] = "A"
    assert (await get_active_state()).view_id == "view-A"
    current["session"] = "B"
    assert (await get_active_state()).view_id == "view-B"


async def test_get_active_state_raises_and_prunes_after_state_expiry(monkeypatch):
    # If the view's stored state expired (TTL) while the session pointer lingers,
    # get_active_state must NOT resurrect a blank default (a mutation would persist it and
    # report false success) — it must prune the pointer and raise.
    monkeypatch.setattr(_state_mod, "_session_key", lambda: "sess-exp")
    await put_state(PdfViewerState(view_id="view-x", url="https://x.pdf", title="X"))
    assert _state_mod._latest_view_by_session["sess-exp"] == "view-x"

    async def _expired_get(**_kwargs):
        return None

    monkeypatch.setattr(_state_mod._store, "get", _expired_get)

    with pytest.raises(LookupError, match="No PDF viewer is open"):
        await get_active_state()
    assert "sess-exp" not in _state_mod._latest_view_by_session  # dangling pointer pruned


async def test_read_and_consume_delivers_then_clears_one_shot_commands():
    # go_to_page / request_fullscreen are one-shot commands: read_and_consume delivers them
    # once (so the client applies them), then clears them in the store WITHOUT bumping the
    # version, so a later unrelated mutation can't re-fire them. search_term is level state
    # and must survive.
    await put_state(
        PdfViewerState(view_id="v1", url="https://x.pdf", go_to_page=4, request_fullscreen=True, search_term="trolldom")
    )
    version = (await get_state("v1")).version

    snap = await _state_mod.read_and_consume("v1")
    assert snap.go_to_page == 4  # delivered
    assert snap.request_fullscreen is True
    assert snap.version == version  # no bump

    after = await get_state("v1")
    assert after.go_to_page == -1  # consumed
    assert after.request_fullscreen is False
    assert after.search_term == "trolldom"  # level state preserved
    assert after.version == version  # still no bump — won't re-trigger the poll

    # A second read is now a no-op for the commands (idempotent).
    assert (await _state_mod.read_and_consume("v1")).go_to_page == -1


async def test_read_and_consume_returns_default_without_writing_on_miss(monkeypatch):
    # No stored state (expired/never-opened) — return a blank default and do NOT write.
    async def _empty_get(**_kwargs):
        return None

    writes: list = []

    async def _spy_put(**kwargs):
        writes.append(kwargs)

    monkeypatch.setattr(_state_mod._store, "get", _empty_get)
    monkeypatch.setattr(_state_mod._store, "put", _spy_put)
    state = await _state_mod.read_and_consume("gone")
    assert state.version == 0
    assert writes == []  # no store write on a miss
