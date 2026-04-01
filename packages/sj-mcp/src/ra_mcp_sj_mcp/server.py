"""Standalone dev server for SJ railway records MCP."""

import argparse
import os

from .tools import sj_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="SJ Railway Records MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3015")))
    args = parser.parse_args()
    if args.stdio:
        sj_mcp.run(transport="stdio")
    else:
        sj_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
