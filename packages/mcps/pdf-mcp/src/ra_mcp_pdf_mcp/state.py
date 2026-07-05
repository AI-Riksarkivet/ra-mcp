"""Per-view session state for the PDF Viewer MCP App.

Each display_pdf call creates a unique PdfViewerState keyed by view_id.
The viewer iframe polls get_pdf_state to detect LLM-initiated changes
(search_term, go_to_page). State auto-expires after TTL.
"""

from __future__ import annotations

from fastmcp.server.dependencies import get_context
from key_value.aio.stores.memory import MemoryStore

from ra_mcp_pdf_mcp.models import PdfViewerState


_COL = "pdf_viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

# "Active view" pointer, scoped per MCP session. Over the HTTP transport one process
# serves many sessions; a single global would let one session's display_pdf hijack the
# no-view_id mutation tools (pdf_go_to_page/pdf_set_search) of another session. Keyed by
# session id; "" is the stdio / no-session bucket.
_latest_view_by_session: dict[str, str] = {}


def _session_key() -> str:
    try:
        return get_context().session_id or ""
    except (RuntimeError, LookupError):
        return ""


async def get_state(view_id: str) -> PdfViewerState:
    data = await _store.get(key=view_id, collection=_COL)
    if data:
        return PdfViewerState.model_validate(data)
    return PdfViewerState(view_id=view_id)


async def read_and_consume(view_id: str) -> PdfViewerState:
    """Return the state for the polling client, clearing the one-shot command fields
    (go_to_page, request_fullscreen) in the store so they apply exactly once.

    search_term is deliberately NOT consumed — it is level state (the active search), not
    a one-shot command. Without consuming go_to_page/request_fullscreen, a later unrelated
    mutation re-emits the still-set value and re-navigates / re-forces fullscreen. The clear
    does not bump the version; the returned snapshot still carries the values for this
    delivery, and re-issuing the command re-sets the field + bumps the version.
    """
    data = await _store.get(key=view_id, collection=_COL)
    if not data:
        return PdfViewerState(view_id=view_id)
    state = PdfViewerState.model_validate(data)
    if state.go_to_page != -1 or state.request_fullscreen:
        snapshot = state.model_copy()
        state.go_to_page = -1
        state.request_fullscreen = False
        await _store.put(key=view_id, value=state.model_dump(), collection=_COL, ttl=_TTL)
        return snapshot
    return state


async def get_active_state() -> PdfViewerState:
    """Get the current session's viewer state. Raises LookupError if no viewer is open."""
    session = _session_key()
    view_id = _latest_view_by_session.get(session, "")
    if not view_id:
        raise LookupError("No PDF viewer is open.")
    data = await _store.get(key=view_id, collection=_COL)
    if not data:
        # The view's stored state expired (TTL) or was evicted. Don't resurrect a blank
        # default here — a mutation tool would persist it and report false success. Drop
        # the now-dangling session pointer (also keeps this dict from accumulating) and
        # signal that no viewer is open.
        _latest_view_by_session.pop(session, None)
        raise LookupError("No PDF viewer is open.")
    return PdfViewerState.model_validate(data)


async def put_state(state: PdfViewerState) -> dict:
    """Bump version, persist, and track as this session's latest. Returns dict for structuredContent."""
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection=_COL, ttl=_TTL)
    _latest_view_by_session[_session_key()] = state.view_id
    return data
