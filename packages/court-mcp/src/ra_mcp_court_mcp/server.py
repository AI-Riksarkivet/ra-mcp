"""Standalone dev server for court records MCP."""

import argparse
import os

from .tools import court_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Court Records MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3008")))
    args = parser.parse_args()
    if args.stdio:
        court_mcp.run(transport="stdio")
    else:
        court_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
