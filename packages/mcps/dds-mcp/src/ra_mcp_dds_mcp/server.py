"""Standalone dev server for DDS church records MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import dds_mcp


def main() -> None:
    run_dev_server(dds_mcp, description="DDS Church Records MCP Server", default_port=3013)


if __name__ == "__main__":
    main()
