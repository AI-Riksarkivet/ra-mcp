"""Standalone dev server for Wincars MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import wincars_mcp


def main() -> None:
    run_dev_server(wincars_mcp, description="Wincars MCP Server", default_port=3014)


if __name__ == "__main__":
    main()
