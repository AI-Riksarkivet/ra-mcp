"""Standalone dev server for Rosenberg MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import rosenberg_mcp


def main() -> None:
    run_dev_server(rosenberg_mcp, description="Rosenberg MCP Server", default_port=3007)


if __name__ == "__main__":
    main()
