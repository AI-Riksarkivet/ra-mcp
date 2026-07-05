"""Shared standalone dev-server entrypoint for the MCP packages.

Every ``*-mcp`` package ships a ``python -m ...server`` entrypoint for isolated
dev/testing whose body is the same argparse + stdio-vs-streamable-http branch,
differing only in the server object, its description, and the default port. This
owns that boilerplate so each package's ``server.py`` is a one-line ``main()``.
"""

from __future__ import annotations

import argparse
import os
from typing import Protocol


class _RunnableServer(Protocol):
    """The FastMCP-style ``run()`` surface this entrypoint needs (kept structural
    so ``ra_mcp_common`` stays fastmcp-free)."""

    def run(self, **kwargs: object) -> None: ...


def run_dev_server(mcp: _RunnableServer, *, description: str, default_port: int) -> None:
    """Parse ``--stdio`` / ``--port`` and run ``mcp`` for local dev/testing.

    ``--stdio`` runs over stdio; otherwise it serves streamable-HTTP on
    ``0.0.0.0:<port>/mcp``, where ``port`` comes from ``--port``, else ``$PORT``,
    else ``default_port``. ``mcp`` is any object with a FastMCP-style ``run()``
    (passed in, so this module stays fastmcp-free).
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", str(default_port))))
    args = parser.parse_args()
    if args.stdio:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")
