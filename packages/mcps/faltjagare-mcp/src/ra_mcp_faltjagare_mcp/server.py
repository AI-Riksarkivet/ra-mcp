"""Standalone dev server for Fältjägare MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import faltjagare_mcp


def main() -> None:
    run_dev_server(faltjagare_mcp, description="Fältjägare MCP Server", default_port=3010)


if __name__ == "__main__":
    main()
