"""Standalone dev server for SJ railway records MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import sj_mcp


def main() -> None:
    run_dev_server(sj_mcp, description="SJ Railway Records MCP Server", default_port=3015)


if __name__ == "__main__":
    main()
