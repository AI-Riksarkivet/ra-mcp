"""Per-view session state for the Document Viewer MCP App.

Each view_document/view_document_urls call creates a unique ViewerState keyed
by view_id. The View iframe polls get_viewer_state with its view_id to detect
LLM-initiated changes (highlight, navigate). State auto-expires after TTL.
"""

from fastmcp.server.dependencies import get_context
from key_value.aio.stores.memory import MemoryStore

from ra_mcp_viewer_mcp.models import ViewerState


_COL = "viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

# "Active view" pointer, scoped per MCP session. Over the HTTP transport one process
# serves many sessions; a single global would let one session's view_document hijack the
# no-view_id mutation tools (viewer_go_to_page/set_highlight/navigate) of another session.
# Keyed by session id; "" is the stdio / no-session bucket.
_latest_view_by_session: dict[str, str] = {}


def _session_key() -> str:
    try:
        return get_context().session_id or ""
    except (RuntimeError, LookupError):
        return ""


async def get_state(view_id: str) -> ViewerState:
    data = await _store.get(key=view_id, collection=_COL)
    if data:
        return ViewerState.model_validate(data)
    return ViewerState(view_id=view_id)


async def read_and_consume(view_id: str) -> ViewerState:
    """Return the state for the polling client, clearing the one-shot command fields
    (go_to_page, request_fullscreen) in the store so they apply exactly once.

    These are imperative commands embedded in polled state: without consuming them, a later
    unrelated mutation re-emits the still-set value and re-navigates / re-forces fullscreen.
    The clear does NOT bump the version (so it can't re-trigger a poll), and the returned
    snapshot still carries the command values for this one delivery. Re-issuing the command
    re-sets the field and bumps the version, so it fires again.
    """
    data = await _store.get(key=view_id, collection=_COL)
    if not data:
        return ViewerState(view_id=view_id)
    state = ViewerState.model_validate(data)
    if state.go_to_page != -1 or state.request_fullscreen:
        snapshot = state.model_copy()
        state.go_to_page = -1
        state.request_fullscreen = False
        await _store.put(key=view_id, value=state.model_dump(), collection=_COL, ttl=_TTL)
        return snapshot
    return state


async def get_active_state() -> ViewerState:
    """Get the current session's viewer state. Raises LookupError if no viewer is open."""
    session = _session_key()
    view_id = _latest_view_by_session.get(session, "")
    if not view_id:
        raise LookupError("No viewer is open.")
    data = await _store.get(key=view_id, collection=_COL)
    if not data:
        # The view's stored state expired (TTL) or was evicted. Don't resurrect a blank
        # default here — a mutation tool would persist it and report false success. Drop
        # the now-dangling session pointer (also keeps this dict from accumulating) and
        # signal that no viewer is open.
        _latest_view_by_session.pop(session, None)
        raise LookupError("No viewer is open.")
    return ViewerState.model_validate(data)


async def require_state(view_id: str) -> ViewerState:
    """Load a view by its explicit id, raising LookupError if it is not in the store.

    Unlike get_state (which returns a blank default for an unknown id), this never
    invents an empty state — so a mutation tool handed a stale/unknown view_id fails
    loudly instead of persisting a blank state and reporting false success.
    """
    data = await _store.get(key=view_id, collection=_COL)
    if not data:
        raise LookupError("No viewer is open.")
    return ViewerState.model_validate(data)


async def resolve_state(view_id: str | None) -> ViewerState:
    """Resolve the target view for a mutation tool.

    Prefer an explicit view_id (the open tool returns it): this works regardless of
    session, so navigate/highlight survive a transport that does not keep a stable MCP
    session_id across tool calls — the root cause of "No viewer is open" on the control
    tools. Fall back to the per-session active-view pointer only when no view_id is given
    (e.g. stdio, where the session is stable).
    """
    if view_id:
        return await require_state(view_id)
    return await get_active_state()


async def put_state(state: ViewerState) -> dict:
    """Bump version, persist, and track as this session's latest. Returns dict for structuredContent."""
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection=_COL, ttl=_TTL)
    _latest_view_by_session[_session_key()] = state.view_id
    return data
