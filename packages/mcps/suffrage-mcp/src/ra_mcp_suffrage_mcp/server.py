"""Standalone dev server for Suffrage MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import suffrage_mcp


def main() -> None:
    run_dev_server(suffrage_mcp, description="Suffrage MCP Server", default_port=3011)


if __name__ == "__main__":
    main()
