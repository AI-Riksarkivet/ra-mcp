"""Standalone dev server for Rosenberg MCP."""

import argparse
import os

from .tools import rosenberg_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Rosenberg MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3007")))
    args = parser.parse_args()
    if args.stdio:
        rosenberg_mcp.run(transport="stdio")
    else:
        rosenberg_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
