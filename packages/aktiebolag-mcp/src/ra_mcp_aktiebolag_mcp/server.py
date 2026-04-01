"""Standalone dev server for Aktiebolag MCP."""

import argparse
import os

from .tools import aktiebolag_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Aktiebolag MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3009")))
    args = parser.parse_args()
    if args.stdio:
        aktiebolag_mcp.run(transport="stdio")
    else:
        aktiebolag_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
