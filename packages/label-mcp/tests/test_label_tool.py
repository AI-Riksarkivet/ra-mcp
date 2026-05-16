"""Tests for ra_mcp_label_mcp.label_tool."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ra_mcp_label_mcp.label_tool import _build_image_only_tasks
from ra_mcp_label_mcp.tools import label_mcp


# ---------------------------------------------------------------------------
# _build_image_only_tasks
# ---------------------------------------------------------------------------


def test_build_image_only_tasks_single():
    tasks = _build_image_only_tasks(["https://img.test/1.jpg"])
    assert tasks == [{"data": {"ocr": "https://img.test/1.jpg"}}]


def test_build_image_only_tasks_multiple():
    tasks = _build_image_only_tasks(["https://img.test/1.jpg", "https://img.test/2.jpg"])
    assert len(tasks) == 2
    assert tasks[1]["data"]["ocr"] == "https://img.test/2.jpg"


def test_build_image_only_tasks_empty():
    assert _build_image_only_tasks([]) == []


# ---------------------------------------------------------------------------
# MCP tool — dry_run mode (no Label Studio needed)
# ---------------------------------------------------------------------------


async def test_tool_dry_run_image_only():
    async with Client(label_mcp) as client:
        result = await client.call_tool(
            "import_to_label_studio",
            {
                "image_urls": ["https://img.test/1.jpg", "https://img.test/2.jpg"],
                "dry_run": True,
            },
        )
    text = result.content[0].text
    tasks = json.loads(text)
    assert len(tasks) == 2
    assert tasks[0]["data"]["ocr"] == "https://img.test/1.jpg"
    assert "predictions" not in tasks[0]


async def test_tool_dry_run_with_alto():
    alto_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation><fileName>p.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="500" HEIGHT="500">
      <PrintSpace>
        <TextBlock>
          <TextLine ID="l1" HPOS="0" VPOS="0" WIDTH="100" HEIGHT="20">
            <Shape><Polygon POINTS="0,0 100,0 100,20 0,20"/></Shape>
            <String CONTENT="Test"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>
"""
    import httpx

    mock_response = httpx.Response(200, text=alto_xml, request=httpx.Request("GET", "https://alto.test/1.xml"))

    with patch("ra_mcp_label_mcp.label_tool.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        async with Client(label_mcp) as client:
            result = await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "alto_urls": ["https://alto.test/1.xml"],
                    "dry_run": True,
                },
            )

    text = result.content[0].text
    tasks = json.loads(text)
    assert len(tasks) == 1
    assert "predictions" in tasks[0]
    assert tasks[0]["data"]["ocr"] == "https://img.test/1.jpg"


# ---------------------------------------------------------------------------
# MCP tool — validation errors (ToolError raised by fastmcp Client)
# ---------------------------------------------------------------------------


async def test_tool_mismatched_alto_image_urls():
    with pytest.raises(ToolError, match="same length"):
        async with Client(label_mcp) as client:
            await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "alto_urls": ["https://alto.test/1.xml", "https://alto.test/2.xml"],
                    "dry_run": True,
                },
            )


async def test_tool_feedback_without_alto_raises():
    with pytest.raises(ToolError, match="requires alto_urls"):
        async with Client(label_mcp) as client:
            await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "feedback": [["Transcription"]],
                    "dry_run": True,
                },
            )


async def test_tool_mismatched_feedback_length():
    with pytest.raises(ToolError, match="same length"):
        async with Client(label_mcp) as client:
            await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "alto_urls": ["https://alto.test/1.xml"],
                    "feedback": [["Transcription"], ["Segmentation"]],
                    "dry_run": True,
                },
            )


# ---------------------------------------------------------------------------
# MCP tool — missing credentials (non-dry-run)
# ---------------------------------------------------------------------------


async def test_tool_missing_ls_url():
    env = {k: v for k, v in os.environ.items() if k not in ("LS_URL", "LS_TOKEN", "LS_PROJECT_ID")}
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ToolError, match="(?i)url required"):
            async with Client(label_mcp) as client:
                await client.call_tool(
                    "import_to_label_studio",
                    {"image_urls": ["https://img.test/1.jpg"]},
                )


async def test_tool_missing_token():
    env = {k: v for k, v in os.environ.items() if k not in ("LS_TOKEN", "LS_PROJECT_ID")}
    env["LS_URL"] = "https://ls.test"
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ToolError, match="(?i)token required"):
            async with Client(label_mcp) as client:
                await client.call_tool(
                    "import_to_label_studio",
                    {"image_urls": ["https://img.test/1.jpg"]},
                )


async def test_tool_missing_project_id():
    env = {k: v for k, v in os.environ.items() if k not in ("LS_PROJECT_ID",)}
    env["LS_URL"] = "https://ls.test"
    env["LS_TOKEN"] = "abc"
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ToolError, match="(?i)project id required"):
            async with Client(label_mcp) as client:
                await client.call_tool(
                    "import_to_label_studio",
                    {"image_urls": ["https://img.test/1.jpg"]},
                )


# ---------------------------------------------------------------------------
# MCP tool — successful import (mocked Label Studio SDK)
# ---------------------------------------------------------------------------


async def test_tool_import_success():
    with (
        patch.dict(
            "os.environ",
            {"LS_URL": "https://ls.test", "LS_TOKEN": "tok", "LS_PROJECT_ID": "99"},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.import_tasks",
            return_value={"task_count": 2, "task_ids": [1, 2]},
        ),
    ):
        async with Client(label_mcp) as client:
            result = await client.call_tool(
                "import_to_label_studio",
                {"image_urls": ["https://img.test/1.jpg", "https://img.test/2.jpg"]},
            )
    text = result.content[0].text
    assert "Successfully imported 2" in text
    assert "project 99" in text
    assert "/projects/99/data?task=1" in text
    assert "/projects/99/data?task=2" in text


async def test_tool_import_with_assignment():
    with (
        patch.dict(
            "os.environ",
            {"LS_URL": "https://ls.test", "LS_TOKEN": "tok", "LS_PROJECT_ID": "5"},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.import_tasks",
            return_value={"task_count": 1, "task_ids": [42]},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.assign_tasks",
            return_value="Alice Smith",
        ),
    ):
        async with Client(label_mcp) as client:
            result = await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "assign_to": "alice@example.com",
                },
            )
    text = result.content[0].text
    assert "Alice Smith" in text


async def test_tool_import_assignment_failure_non_fatal():
    with (
        patch.dict(
            "os.environ",
            {"LS_URL": "https://ls.test", "LS_TOKEN": "tok", "LS_PROJECT_ID": "5"},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.import_tasks",
            return_value={"task_count": 1, "task_ids": [42]},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.assign_tasks",
            side_effect=RuntimeError("user not found"),
        ),
    ):
        async with Client(label_mcp) as client:
            result = await client.call_tool(
                "import_to_label_studio",
                {
                    "image_urls": ["https://img.test/1.jpg"],
                    "assign_to": "nobody@example.com",
                },
            )
    text = result.content[0].text
    assert "Successfully imported" in text
    assert "Assignment failed" in text


async def test_tool_import_api_error():
    with (
        patch.dict(
            "os.environ",
            {"LS_URL": "https://ls.test", "LS_TOKEN": "tok", "LS_PROJECT_ID": "5"},
        ),
        patch(
            "ra_mcp_label_mcp.label_tool.import_tasks",
            side_effect=RuntimeError("API error 500"),
        ),
    ):
        with pytest.raises(ToolError, match="API error 500"):
            async with Client(label_mcp) as client:
                await client.call_tool(
                    "import_to_label_studio",
                    {"image_urls": ["https://img.test/1.jpg"]},
                )
