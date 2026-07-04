"""Standalone dev server for TORA MCP."""

import argparse
import os

from .tools import tora_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="TORA MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3020")))
    args = parser.parse_args()
    if args.stdio:
        tora_mcp.run(transport="stdio")
    else:
        tora_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
