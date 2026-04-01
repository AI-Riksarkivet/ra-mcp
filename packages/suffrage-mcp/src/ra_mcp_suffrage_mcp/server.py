"""Standalone dev server for Suffrage MCP."""

import argparse
import os

from .tools import suffrage_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Suffrage MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3011")))
    args = parser.parse_args()
    if args.stdio:
        suffrage_mcp.run(transport="stdio")
    else:
        suffrage_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
