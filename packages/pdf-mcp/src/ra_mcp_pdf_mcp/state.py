"""Per-view session state and command queue for the PDF Viewer MCP App.

Each display_pdf call creates a unique PdfViewerState keyed by view_id.
The viewer iframe polls get_pdf_state to detect LLM-initiated changes.
Commands (from interact tool) are queued and delivered via poll_pdf_commands.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import defaultdict

from key_value.aio.stores.memory import MemoryStore

from ra_mcp_pdf_mcp.models import PdfCommand, PdfViewerState


_COL = "pdf_viewer_state"
_TTL = 600  # 10 min
_store = MemoryStore(max_entries_per_collection=64)

latest_view_id: str = ""


# Command queues: view_id → list of pending commands
_command_queues: dict[str, list[dict]] = defaultdict(list)
_command_events: dict[str, asyncio.Event] = {}


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


def enqueue_command(view_id: str, command: PdfCommand) -> None:
    """Add a command to the queue for a specific view."""
    _command_queues[view_id].append(command.model_dump(exclude_none=True))
    # Signal any waiting poll
    event = _command_events.get(view_id)
    if event:
        event.set()


async def dequeue_commands(view_id: str, timeout: float = 30.0) -> list[dict]:
    """Dequeue all pending commands for a view. Long-polls if empty."""
    queue = _command_queues.get(view_id, [])
    if queue:
        commands = list(queue)
        queue.clear()
        return commands

    # Long-poll: wait for a command or timeout
    event = _command_events.get(view_id)
    if not event:
        event = asyncio.Event()
        _command_events[view_id] = event

    event.clear()
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(event.wait(), timeout=timeout)

    # Drain whatever accumulated during the wait
    queue = _command_queues.get(view_id, [])
    commands = list(queue)
    queue.clear()
    return commands
