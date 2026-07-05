"""Standalone dev server for TORA MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import tora_mcp


def main() -> None:
    run_dev_server(tora_mcp, description="TORA MCP Server", default_port=3020)


if __name__ == "__main__":
    main()
