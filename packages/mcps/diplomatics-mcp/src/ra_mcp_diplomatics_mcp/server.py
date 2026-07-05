"""Standalone dev server for diplomatics MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import diplomatics_mcp


def main() -> None:
    run_dev_server(diplomatics_mcp, description="Diplomatics MCP Server", default_port=3003)


if __name__ == "__main__":
    main()
