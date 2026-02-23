"""
Label Studio API client for importing tasks.

Uses the official Label Studio SDK which handles both legacy tokens
and Personal Access Tokens (JWT PATs) transparently.
"""

import logging

from label_studio_sdk import LabelStudio
from label_studio_sdk.core.api_error import ApiError


logger = logging.getLogger("ra_mcp.label.client")


def import_tasks(tasks: list[dict], ls_url: str, token: str, project_id: int) -> dict:
    """Import Label Studio tasks via the SDK.

    Args:
        tasks: List of Label Studio task dicts.
        ls_url: Label Studio instance URL (e.g. https://your-ls.hf.space).
        token: Label Studio access token (legacy hex or JWT PAT).
        project_id: Target project ID.

    Returns:
        Dict with import result including task_count.

    Raises:
        RuntimeError: On API errors.
    """
    try:
        client = LabelStudio(base_url=ls_url.rstrip("/"), api_key=token.strip())
        result = client.projects.import_tasks(id=project_id, request=tasks)
        count = getattr(result, "task_count", None) or len(tasks)
        logger.info(f"Imported {count} task(s) to project {project_id}")
        return {"task_count": count}
    except ApiError as e:
        raise RuntimeError(f"Label Studio API error {e.status_code}: {e.body}") from e
    except Exception as e:
        raise RuntimeError(f"Label Studio API request failed: {e}") from e
