"""Standalone dev server for Specialsök MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import specialsok_mcp


def main() -> None:
    run_dev_server(specialsok_mcp, description="Specialsök MCP Server", default_port=3012)


if __name__ == "__main__":
    main()
