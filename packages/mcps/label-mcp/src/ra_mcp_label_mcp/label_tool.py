"""
Label Studio MCP tool for importing pages as annotation tasks.

Provides the import_to_label_studio tool that supports two modes:
- With ALTO XML: fetches ALTO, converts to VectorLabels pre-annotations, and imports
- Images only: creates blank tasks for annotation from scratch
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Annotated

import httpx
from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from ra_mcp_label_mcp.converter import convert_alto_to_tasks, tasks_to_json
from ra_mcp_label_mcp.ls_client import assign_tasks, import_tasks


logger = logging.getLogger("ra_mcp.label.tool")


# Auto-load .env from the package directory
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_file.is_file():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _build_image_only_tasks(image_urls: list[str]) -> list[dict]:
    """Create minimal Label Studio tasks with only image data (no pre-annotations)."""
    return [{"data": {"ocr": url}} for url in image_urls]


def register_label_tool(mcp) -> None:
    """Register the label tool with the MCP server."""

    @mcp.tool(
        name="import_to_label_studio",
        version="1.0",
        timeout=120.0,
        tags={"label-studio"},
        annotations={
            "title": "Import Pages to Label Studio",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def import_to_label_studio(
        image_urls: Annotated[list[str], Field(description="Image URLs to import (one per page).")],
        alto_urls: Annotated[
            list[str] | None,
            Field(
                description="ALTO XML URLs paired by index with image_urls. If provided, creates pre-annotated tasks with VectorLabels polygons and transcriptions. If omitted, creates blank tasks for annotation from scratch."
            ),
        ] = None,
        feedback: Annotated[
            list[list[str]] | None,
            Field(
                description="Feedback choices per page, paired by index. Values: 'Transcription', 'Segmentation'. "
                "Example: [['Transcription'], [], ['Transcription', 'Segmentation']]. Only used with alto_urls."
            ),
        ] = None,
        ls_url: Annotated[str | None, Field(description="Label Studio URL (e.g. 'https://your-ls.hf.space'). Falls back to LS_URL env var.")] = None,
        ls_token: Annotated[str | None, Field(description="Label Studio access token. Falls back to LS_TOKEN env var.")] = None,
        project_id: Annotated[int | None, Field(description="Label Studio project ID. Falls back to LS_PROJECT_ID env var.")] = None,
        assign_to: Annotated[
            str | None, Field(description="Email of a Label Studio user to assign the imported tasks to for annotation. If omitted, tasks are unassigned.")
        ] = None,
        dry_run: Annotated[bool, Field(description="If true, return converted JSON without importing to Label Studio.")] = False,
        ctx: Context | None = None,
    ) -> str:
        """Import pages to a Label Studio project for human annotation.

        Two modes:
        - With alto_urls: fetches ALTO XML, converts to pre-annotated tasks with polygons and transcriptions
        - Without alto_urls: creates blank tasks with just the image for annotation from scratch

        Set dry_run=true to preview the converted tasks without importing.
        """
        if alto_urls and len(alto_urls) != len(image_urls):
            raise ToolError(f"alto_urls ({len(alto_urls)}) and image_urls ({len(image_urls)}) must have the same length")
        if feedback and alto_urls and len(feedback) != len(alto_urls):
            raise ToolError(f"feedback ({len(feedback)}) must have the same length as alto_urls ({len(alto_urls)})")
        if feedback and not alto_urls:
            raise ToolError("feedback requires alto_urls (feedback choices are attached to ALTO text regions)")

        if alto_urls:
            tasks = await _fetch_and_convert_alto(alto_urls, image_urls, feedback)
        else:
            logger.info("Creating %d image-only task(s) (no pre-annotations)", len(image_urls))
            tasks = _build_image_only_tasks(image_urls)

        # Dry run — return JSON preview
        if dry_run:
            logger.info("Dry run: returning %d task(s) as JSON", len(tasks))
            return tasks_to_json(tasks)

        # Import to Label Studio
        url = (ls_url or os.getenv("LS_URL", "")).strip() or None
        token = (ls_token or os.getenv("LS_TOKEN", "")).strip() or None
        pid = project_id or (int(v) if (v := os.getenv("LS_PROJECT_ID")) else None)

        if not url:
            raise ToolError("Label Studio URL required (pass ls_url or set LS_URL env var)")
        if not token:
            raise ToolError("Label Studio token required (pass ls_token or set LS_TOKEN env var)")
        if not pid:
            raise ToolError("Project ID required (pass project_id or set LS_PROJECT_ID env var)")

        mode = "pre-annotated" if alto_urls else "image-only"
        logger.info("Importing %d %s task(s) to project %d at %s", len(tasks), mode, pid, url)

        try:
            result = await asyncio.to_thread(import_tasks, tasks, url, token, pid)
        except RuntimeError as e:
            raise ToolError(str(e)) from e

        count = result.get("task_count", len(tasks))
        task_ids = result.get("task_ids", [])
        logger.info("Successfully imported %d task(s) to project %d", count, pid)

        base = url.rstrip("/")
        lines = [f"Successfully imported {count} {mode} task(s) to project {pid}"]

        # Optionally assign tasks to a user
        if assign_to and task_ids:
            try:
                assignee = await asyncio.to_thread(assign_tasks, task_ids, assign_to, url, token, pid)
                lines.append(f"Assigned to: {assignee}")
            except RuntimeError as e:
                lines.append(f"Assignment failed: {e}")

        if task_ids:
            lines.append("")
            lines.append("Label Studio task links:")
            lines.extend(f"  - {base}/projects/{pid}/data?task={tid}" for tid in task_ids)
        return "\n".join(lines)


async def _fetch_and_convert_alto(
    alto_urls: list[str],
    image_urls: list[str],
    feedback: list[list[str]] | None,
) -> list[dict]:
    """Fetch ALTO XMLs and convert to pre-annotated Label Studio tasks."""
    logger.info("Fetching %d ALTO XML page(s)", len(alto_urls))

    alto_xmls: list[str] = []
    paired_image_urls: list[str] = []
    paired_feedback: list[list[str]] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for i, url in enumerate(alto_urls):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                alto_xmls.append(resp.text)
                paired_image_urls.append(image_urls[i])
                paired_feedback.append(feedback[i] if feedback else [])
            except httpx.HTTPError as e:
                logger.warning("Failed to fetch ALTO URL %s: %s", url, e)

    if not alto_xmls:
        raise ToolError("Failed to fetch any ALTO XML from the provided URLs")

    logger.info("Converting %d ALTO page(s) to Label Studio tasks", len(alto_xmls))

    try:
        return convert_alto_to_tasks(
            alto_xmls,
            image_urls=paired_image_urls,
            feedback_list=paired_feedback or None,
        )
    except Exception as e:
        raise ToolError(f"ALTO conversion failed: {e}") from e
