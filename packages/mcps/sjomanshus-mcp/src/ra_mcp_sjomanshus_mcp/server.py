"""Standalone dev server for Sjömanshus MCP."""

from ra_mcp_common.dev_server import run_dev_server

from .tools import sjomanshus_mcp


def main() -> None:
    run_dev_server(sjomanshus_mcp, description="Sjömanshus MCP Server", default_port=3005)


if __name__ == "__main__":
    main()
