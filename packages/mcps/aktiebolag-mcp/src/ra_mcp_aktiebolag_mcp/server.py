"""Standalone dev server for Aktiebolag MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import aktiebolag_mcp


def main() -> None:
    run_dev_server(aktiebolag_mcp, description="Aktiebolag MCP Server", default_port=3009)


if __name__ == "__main__":
    main()
