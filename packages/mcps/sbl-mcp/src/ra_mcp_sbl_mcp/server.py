"""Standalone dev server for SBL MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import sbl_mcp


def main() -> None:
    run_dev_server(sbl_mcp, description="SBL MCP Server", default_port=3004)


if __name__ == "__main__":
    main()
