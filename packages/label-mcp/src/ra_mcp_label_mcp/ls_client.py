"""
Label Studio API client for importing tasks.
"""

import logging

import httpx


logger = logging.getLogger("ra_mcp.label.client")


async def import_tasks(tasks: list[dict], ls_url: str, token: str, project_id: int) -> dict:
    """Import Label Studio tasks via the API.

    Args:
        tasks: List of Label Studio task dicts.
        ls_url: Label Studio instance URL (e.g. https://your-ls.hf.space).
        token: Label Studio access token.
        project_id: Target project ID.

    Returns:
        API response dict.

    Raises:
        RuntimeError: On API errors.
    """
    url = f"{ls_url.rstrip('/')}/api/projects/{project_id}/import"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                url,
                json=tasks,
                headers={"Authorization": f"Token {token}"},
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            count = result.get("task_count", len(tasks))
            logger.info(f"Imported {count} task(s) to project {project_id}")
            return result
        except httpx.HTTPStatusError as e:
            body = e.response.text
            raise RuntimeError(f"Label Studio API error {e.response.status_code}: {body}") from e
        except httpx.HTTPError as e:
            raise RuntimeError(f"Label Studio API request failed: {e}") from e
