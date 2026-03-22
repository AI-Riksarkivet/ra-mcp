"""Per-view session state for the Document Viewer MCP App.

Each view_document/view_document_urls call creates a unique ViewerState keyed
by view_id. The View iframe polls get_viewer_state with its view_id to detect
LLM-initiated changes (highlight, navigate). State auto-expires after TTL.
"""

from key_value.aio.stores.memory import MemoryStore
from pydantic import BaseModel


_COL = "viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

latest_view_id: str = ""


class ViewerState(BaseModel):
    """Per-view state keyed by view_id. Polled by the View iframe via get_viewer_state."""

    view_id: str = ""
    version: int = 0
    image_urls: list[str] = []
    text_layer_urls: list[str] = []
    page_numbers: list[int] = []
    highlight_term: str = ""
    reference_code: str = ""
    go_to_page: int = -1  # -1 = no navigation request, 0+ = jump to this page index


async def get_state(view_id: str) -> ViewerState:
    data = await _store.get(key=view_id, collection=_COL)
    if data:
        return ViewerState.model_validate(data)
    return ViewerState(view_id=view_id)


async def put_state(state: ViewerState) -> dict:
    """Bump version, persist, and track as latest. Returns dict for structuredContent."""
    global latest_view_id
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection=_COL, ttl=_TTL)
    latest_view_id = state.view_id
    return data
