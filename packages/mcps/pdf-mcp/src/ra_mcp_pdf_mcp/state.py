"""Per-view session state for the PDF Viewer MCP App.

Each display_pdf call creates a unique PdfViewerState keyed by view_id.
The viewer iframe polls get_pdf_state to detect LLM-initiated changes
(search_term, go_to_page). State auto-expires after TTL.
"""

from __future__ import annotations

from key_value.aio.stores.memory import MemoryStore

from ra_mcp_pdf_mcp.models import PdfViewerState


_COL = "pdf_viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

latest_view_id: str = ""


async def get_state(view_id: str) -> PdfViewerState:
    data = await _store.get(key=view_id, collection=_COL)
    if data:
        return PdfViewerState.model_validate(data)
    return PdfViewerState(view_id=view_id)


async def get_active_state() -> PdfViewerState:
    """Get the current viewer state. Raises LookupError if no viewer is open."""
    if not latest_view_id:
        raise LookupError("No PDF viewer is open.")
    return await get_state(latest_view_id)


async def put_state(state: PdfViewerState) -> dict:
    """Bump version, persist, and track as latest. Returns dict for structuredContent."""
    global latest_view_id
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection=_COL, ttl=_TTL)
    latest_view_id = state.view_id
    return data
