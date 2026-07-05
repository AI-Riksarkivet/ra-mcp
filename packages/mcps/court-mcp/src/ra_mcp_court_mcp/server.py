"""Standalone dev server for court records MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import court_mcp


def main() -> None:
    run_dev_server(court_mcp, description="Court Records MCP Server", default_port=3008)


if __name__ == "__main__":
    main()
