"""
RA-MCP Server
Main entry point for the Riksarkivet MCP server.
"""
from mcp_tools import ra_mcp


def main():
    """Main entry point for the server."""
    import argparse

    parser = argparse.ArgumentParser(description="Riksarkivet MCP Server")
    parser.add_argument(
        "--http", action="store_true", help="Use HTTP/SSE transport instead of stdio"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for HTTP transport (default: localhost)",
    )

    args = parser.parse_args()

    if args.http:
        print(f"Starting RA-MCP HTTP/SSE server on http://{args.host}:{args.port}")
        print(
            f"Connect with: claude mcp add --transport sse ra-mcp http://{args.host}:{args.port}/sse"
        )
        ra_mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        print("Starting RA-MCP stdio server")
        print("This mode is for direct integration with Claude Desktop")
        ra_mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
