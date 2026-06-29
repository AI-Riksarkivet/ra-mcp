# API Reference

Auto-generated reference documentation for all public Python APIs in the ra-mcp workspace.

## Packages

| Package | Description |
|---------|-------------|
| [Common](common.md) | Shared HTTP client and utility functions |
| [Search](search.md) | Search domain (`ra-mcp-search-lib`) — models, client, and operations |
| [Browse](browse.md) | Browse domain (`ra-mcp-browse-lib`) — models, operations, URL generation |
| [MCP Tools](mcp-tools.md) | MCP tool and resource registrations (search, browse, guide, HTR, viewer, PDF, Label Studio, datasets) |

The ALTO, IIIF, and OAI-PMH HTTP clients that browse depends on now live in their own
libraries — **`ra-mcp-xml`** (`ra_mcp_xml`), **`ra-mcp-iiif-lib`** (`ra_mcp_iiif_lib`), and
**`ra-mcp-oai-pmh-lib`** (`ra_mcp_oai_pmh_lib`).

The optional dataset modules (e.g. `ra-mcp-court-mcp`, `ra-mcp-dds-mcp`, `ra-mcp-sbl-mcp`), the
PDF viewer (`ra-mcp-pdf-mcp`), and the Label Studio importer (`ra-mcp-label-mcp`) each expose their
own MCP tools. They are described on the [MCP Tools](mcp-tools.md) page and in the
[Tools reference](../tools/tools.md); their auto-generated API is omitted here because they are
optional and not all are installed in every deployment.
