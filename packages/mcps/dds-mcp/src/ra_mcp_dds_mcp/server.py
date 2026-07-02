"""Standalone dev server for DDS church records MCP."""

import argparse
import os

from .tools import dds_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="DDS Church Records MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3013")))
    args = parser.parse_args()
    if args.stdio:
        dds_mcp.run(transport="stdio")
    else:
        dds_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
