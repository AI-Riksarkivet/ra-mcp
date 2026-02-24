"""
Label Studio API client for importing tasks.

Uses the official Label Studio SDK which handles both legacy tokens
and Personal Access Tokens (JWT PATs) transparently.
"""

import logging

from label_studio_sdk import LabelStudio
from label_studio_sdk.core.api_error import ApiError


logger = logging.getLogger("ra_mcp.label.client")


def _get_client(ls_url: str, token: str) -> LabelStudio:
    """Create a Label Studio SDK client."""
    return LabelStudio(base_url=ls_url.rstrip("/"), api_key=token.strip())


def import_tasks(tasks: list[dict], ls_url: str, token: str, project_id: int) -> dict:
    """Import Label Studio tasks via the SDK.

    Args:
        tasks: List of Label Studio task dicts.
        ls_url: Label Studio instance URL (e.g. https://your-ls.hf.space).
        token: Label Studio access token (legacy hex or JWT PAT).
        project_id: Target project ID.

    Returns:
        Dict with import result including task_count and task_ids.

    Raises:
        RuntimeError: On API errors.
    """
    try:
        client = _get_client(ls_url, token)
        result = client.projects.import_tasks(id=project_id, request=tasks, return_task_ids=True)  # type: ignore[arg-type]  # SDK accepts plain dicts at runtime
        count = getattr(result, "task_count", None) or len(tasks)
        task_ids = getattr(result, "task_ids", None) or []
        logger.info("Imported %d task(s) to project %d (task_ids=%s)", count, project_id, task_ids)
        return {"task_count": count, "task_ids": task_ids}
    except ApiError as e:
        raise RuntimeError(f"Label Studio API error {e.status_code}: {e.body}") from e
    except Exception as e:
        raise RuntimeError(f"Label Studio API request failed: {e}") from e


def assign_tasks(
    task_ids: list[int],
    email: str,
    ls_url: str,
    token: str,
    project_id: int,
) -> str:
    """Assign imported tasks to a user by email.

    Looks up the user by email and bulk-assigns the given tasks for annotation.

    Returns:
        Display name of the assigned user.

    Raises:
        RuntimeError: If user not found or API error.
    """
    try:
        client = _get_client(ls_url, token)

        # Resolve email to user ID
        users = list(client.users.list())
        user = next((u for u in users if (u.email or "").lower() == email.lower()), None)
        if not user:
            raise RuntimeError(f"No Label Studio user found with email: {email}")

        client.projects.assignments.bulk_assign(
            id=project_id,
            type="AN",
            users=[user.id],
            selected_items={"all": False, "included": task_ids},
        )

        name = f"{user.first_name} {user.last_name}".strip() or user.email
        logger.info("Assigned %d task(s) to %s (id=%d)", len(task_ids), name, user.id)
        return name
    except ApiError as e:
        raise RuntimeError(f"Label Studio assignment error {e.status_code}: {e.body}") from e
