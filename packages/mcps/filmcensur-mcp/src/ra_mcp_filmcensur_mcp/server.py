"""Standalone dev server for Filmcensur MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import filmcensur_mcp


def main() -> None:
    run_dev_server(filmcensur_mcp, description="Filmcensur MCP Server", default_port=3006)


if __name__ == "__main__":
    main()
