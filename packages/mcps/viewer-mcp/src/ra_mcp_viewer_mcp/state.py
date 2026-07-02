"""Per-view session state for the Document Viewer MCP App.

Each view_document/view_document_urls call creates a unique ViewerState keyed
by view_id. The View iframe polls get_viewer_state with its view_id to detect
LLM-initiated changes (highlight, navigate). State auto-expires after TTL.
"""

from key_value.aio.stores.memory import MemoryStore

from ra_mcp_viewer_mcp.models import ViewerState


_COL = "viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

latest_view_id: str = ""


async def get_state(view_id: str) -> ViewerState:
    data = await _store.get(key=view_id, collection=_COL)
    if data:
        return ViewerState.model_validate(data)
    return ViewerState(view_id=view_id)


async def get_active_state() -> ViewerState:
    """Get the current viewer state. Raises LookupError if no viewer is open."""
    if not latest_view_id:
        raise LookupError("No viewer is open.")
    return await get_state(latest_view_id)


async def put_state(state: ViewerState) -> dict:
    """Bump version, persist, and track as latest. Returns dict for structuredContent."""
    global latest_view_id
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection=_COL, ttl=_TTL)
    latest_view_id = state.view_id
    return data
