"""Standalone dev server for diplomatics MCP."""

import argparse
import os

from .tools import diplomatics_mcp


def main():
    parser = argparse.ArgumentParser(description="Diplomatics MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3003")))
    args = parser.parse_args()
    if args.stdio:
        diplomatics_mcp.run(transport="stdio")
    else:
        diplomatics_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
