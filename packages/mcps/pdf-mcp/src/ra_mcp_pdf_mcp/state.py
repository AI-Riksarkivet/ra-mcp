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
