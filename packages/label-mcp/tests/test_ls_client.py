"""Tests for ra_mcp_label_mcp.ls_client."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ra_mcp_label_mcp.ls_client import _get_client, assign_tasks, import_tasks


# ---------------------------------------------------------------------------
# _get_client
# ---------------------------------------------------------------------------


def test_get_client_strips_trailing_slash():
    with patch("ra_mcp_label_mcp.ls_client.LabelStudio") as mock_cls:
        _get_client("https://ls.example.com/", "tok123")
        mock_cls.assert_called_once_with(base_url="https://ls.example.com", api_key="tok123")


def test_get_client_strips_token_whitespace():
    with patch("ra_mcp_label_mcp.ls_client.LabelStudio") as mock_cls:
        _get_client("https://ls.example.com", "  tok123  ")
        mock_cls.assert_called_once_with(base_url="https://ls.example.com", api_key="tok123")


# ---------------------------------------------------------------------------
# import_tasks
# ---------------------------------------------------------------------------


def test_import_tasks_success():
    mock_result = SimpleNamespace(task_count=2, task_ids=[10, 11])
    mock_client = MagicMock()
    mock_client.projects.import_tasks.return_value = mock_result

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        result = import_tasks(
            [{"data": {"ocr": "a"}}, {"data": {"ocr": "b"}}],
            "https://ls.example.com",
            "token",
            42,
        )

    assert result == {"task_count": 2, "task_ids": [10, 11]}
    mock_client.projects.import_tasks.assert_called_once_with(
        id=42,
        request=[{"data": {"ocr": "a"}}, {"data": {"ocr": "b"}}],
        return_task_ids=True,
    )


def test_import_tasks_fallback_count():
    mock_result = SimpleNamespace()
    mock_client = MagicMock()
    mock_client.projects.import_tasks.return_value = mock_result

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        result = import_tasks([{"data": {"ocr": "a"}}], "https://ls.example.com", "token", 1)

    assert result["task_count"] == 1
    assert result["task_ids"] == []


def test_import_tasks_api_error():
    from label_studio_sdk.core.api_error import ApiError

    mock_client = MagicMock()
    mock_client.projects.import_tasks.side_effect = ApiError(status_code=403, body="Forbidden")

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Label Studio API error 403"):
            import_tasks([{"data": {"ocr": "a"}}], "https://ls.example.com", "token", 1)


def test_import_tasks_generic_error():
    mock_client = MagicMock()
    mock_client.projects.import_tasks.side_effect = ConnectionError("network down")

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Label Studio API request failed"):
            import_tasks([{"data": {"ocr": "a"}}], "https://ls.example.com", "token", 1)


# ---------------------------------------------------------------------------
# assign_tasks
# ---------------------------------------------------------------------------


def _make_user(user_id, email, first_name="", last_name=""):
    return SimpleNamespace(id=user_id, email=email, first_name=first_name, last_name=last_name)


def test_assign_tasks_success():
    users = [
        _make_user(1, "alice@example.com", "Alice", "Smith"),
        _make_user(2, "bob@example.com", "Bob", "Jones"),
    ]
    mock_client = MagicMock()
    mock_client.users.list.return_value = iter(users)

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        name = assign_tasks([10, 11], "alice@example.com", "https://ls.example.com", "token", 42)

    assert name == "Alice Smith"
    mock_client.projects.assignments.bulk_assign.assert_called_once_with(
        id=42,
        type="AN",
        users=[1],
        selected_items={"all": False, "included": [10, 11]},
    )


def test_assign_tasks_case_insensitive_email():
    users = [_make_user(1, "Alice@Example.COM", "Alice", "")]
    mock_client = MagicMock()
    mock_client.users.list.return_value = iter(users)

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        name = assign_tasks([10], "alice@example.com", "https://ls.example.com", "token", 1)

    assert name == "Alice"


def test_assign_tasks_falls_back_to_email_for_name():
    users = [_make_user(1, "anon@example.com", "", "")]
    mock_client = MagicMock()
    mock_client.users.list.return_value = iter(users)

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        name = assign_tasks([10], "anon@example.com", "https://ls.example.com", "token", 1)

    assert name == "anon@example.com"


def test_assign_tasks_user_not_found():
    mock_client = MagicMock()
    mock_client.users.list.return_value = iter([])

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        with pytest.raises(RuntimeError, match="No Label Studio user found"):
            assign_tasks([10], "nobody@example.com", "https://ls.example.com", "token", 1)


def test_assign_tasks_api_error():
    from label_studio_sdk.core.api_error import ApiError

    users = [_make_user(1, "alice@example.com", "Alice", "")]
    mock_client = MagicMock()
    mock_client.users.list.return_value = iter(users)
    mock_client.projects.assignments.bulk_assign.side_effect = ApiError(status_code=500, body="fail")

    with patch("ra_mcp_label_mcp.ls_client._get_client", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Label Studio assignment error 500"):
            assign_tasks([10], "alice@example.com", "https://ls.example.com", "token", 1)
