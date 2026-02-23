"""
Label Studio MCP Server — Tool registrations.

Tools:
  - alto_to_label_studio: Convert ALTO XML to Label Studio JSON tasks
  - import_to_label_studio: Import tasks to a Label Studio project via API
"""

import logging
import os
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from ra_mcp_label_mcp.converter import convert_alto_to_tasks, tasks_to_json
from ra_mcp_label_mcp.ls_client import import_tasks


logger = logging.getLogger("ra_mcp.label.tools")

label_mcp = FastMCP(
    name="ra-label-mcp",
    instructions="""
    Riksarkivet Label Studio MCP Server

    Converts ALTO XML transcriptions into Label Studio pre-annotation tasks
    using the VectorLabels format. Supports direct import via the Label Studio API.

    AVAILABLE TOOLS:

    alto_to_label_studio - Convert ALTO XML to Label Studio JSON
       - Accepts ALTO XML strings (one per page)
       - Outputs JSON tasks with VectorLabels polygons and transcriptions
       - Optionally set image_base_url to prefix image URLs

    import_to_label_studio - Import tasks to Label Studio via API
       - Takes JSON tasks (output from alto_to_label_studio)
       - Requires Label Studio URL, access token, and project ID
       - Can also be configured via environment variables

    WORKFLOW:
    1. Get ALTO XML from browse_document or search results
    2. Call alto_to_label_studio to convert to Label Studio format
    3. Optionally call import_to_label_studio to push tasks to a project
    """,
)


@label_mcp.tool(
    annotations={
        "title": "Convert ALTO XML to Label Studio Tasks",
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def alto_to_label_studio(
    alto_xmls: Annotated[list[str], Field(description="List of ALTO XML strings (one per page) to convert")],
    image_base_url: Annotated[
        str | None, Field(description="Base URL prefix for page images (e.g. 'https://lbiiif.riksarkivet.se'). Appended with the filename from ALTO.")
    ] = None,
) -> str:
    """Convert ALTO XML pages to Label Studio pre-annotation tasks (VectorLabels format).

    Returns JSON string with Label Studio tasks containing polygon regions
    and transcriptions ready for import.
    """
    try:
        tasks = convert_alto_to_tasks(alto_xmls, image_base_url=image_base_url)
        result = tasks_to_json(tasks)
        logger.info(f"Converted {len(tasks)} ALTO page(s) to Label Studio JSON")
        return result
    except Exception as e:
        raise ToolError(f"ALTO conversion failed: {e}") from e


@label_mcp.tool(
    annotations={
        "title": "Import Tasks to Label Studio",
        "readOnlyHint": False,
        "idempotentHint": False,
    },
)
async def import_to_label_studio(
    tasks_json: Annotated[str, Field(description="JSON string of Label Studio tasks (output from alto_to_label_studio)")],
    ls_url: Annotated[str | None, Field(description="Label Studio URL (e.g. 'https://your-ls.hf.space'). Falls back to LS_URL env var.")] = None,
    ls_token: Annotated[str | None, Field(description="Label Studio access token. Falls back to LS_TOKEN env var.")] = None,
    project_id: Annotated[int | None, Field(description="Label Studio project ID. Falls back to LS_PROJECT_ID env var.")] = None,
) -> str:
    """Import Label Studio tasks into a project via the Label Studio API.

    Requires Label Studio URL, access token, and project ID — either as
    parameters or via environment variables (LS_URL, LS_TOKEN, LS_PROJECT_ID).
    """
    import json

    url = ls_url or os.getenv("LS_URL")
    token = ls_token or os.getenv("LS_TOKEN")
    pid = project_id or (int(v) if (v := os.getenv("LS_PROJECT_ID")) else None)

    if not url:
        raise ToolError("Label Studio URL required (pass ls_url or set LS_URL env var)")
    if not token:
        raise ToolError("Label Studio token required (pass ls_token or set LS_TOKEN env var)")
    if not pid:
        raise ToolError("Project ID required (pass project_id or set LS_PROJECT_ID env var)")

    try:
        tasks = json.loads(tasks_json)
    except json.JSONDecodeError as e:
        raise ToolError(f"Invalid JSON: {e}") from e

    try:
        result = await import_tasks(tasks, url, token, pid)
        count = result.get("task_count", len(tasks))
        logger.info(f"Imported {count} task(s) to project {pid}")
        return f"Successfully imported {count} task(s) to project {pid}"
    except RuntimeError as e:
        raise ToolError(str(e)) from e
