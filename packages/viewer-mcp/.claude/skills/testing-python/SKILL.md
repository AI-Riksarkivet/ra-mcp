---
name: testing-python
description: Write and evaluate effective Python tests using pytest. Use when writing tests, reviewing test code, debugging test failures, or improving test coverage. Covers test design, fixtures, parameterization, mocking, async testing, and CI integration.
---

# Writing Effective Python Tests

## Core Principles

- Every test should be **atomic**, **self-contained**, and test **one behavior**
- Tests should be **deterministic** — no flaky results from shared state, timing, or network
- Test the **contract** (inputs/outputs/errors), not the implementation details
- Prefer **real implementations** over mocks when practical

## Test Structure

### One behavior per test

Each test should verify a single behavior. The test name should tell you what's broken when it fails. Multiple assertions are fine when they all verify the same behavior.

```python
# Good: name tells you what's broken
def test_user_creation_sets_defaults():
    user = User(name="Alice")
    assert user.role == "member"
    assert user.id is not None
    assert user.created_at is not None

# Bad: if this fails, what behavior is broken?
def test_user():
    user = User(name="Alice")
    assert user.role == "member"
    user.promote()
    assert user.role == "admin"
    assert user.can_delete_others()
```

### Arrange-Act-Assert (AAA)

```python
def test_transfer_reduces_sender_balance():
    # Arrange
    sender = Account(balance=100)
    receiver = Account(balance=50)

    # Act
    transfer(sender, receiver, amount=30)

    # Assert
    assert sender.balance == 70
```

### Naming: `test_<subject>_<scenario>`

```python
# Good — describes subject and scenario
def test_login_fails_with_invalid_password(): ...
def test_parse_csv_skips_empty_rows(): ...
def test_cache_expires_after_ttl(): ...

# Bad — too vague
def test_login(): ...
def test_1(): ...
def test_it_works(): ...
```

### Parameterization for variations of the same concept

```python
import pytest

@pytest.mark.parametrize("input_val,expected", [
    pytest.param("hello", "HELLO", id="lowercase"),
    pytest.param("World", "WORLD", id="mixed-case"),
    pytest.param("", "", id="empty-string"),
    pytest.param("123", "123", id="digits-unchanged"),
])
def test_uppercase_conversion(input_val, expected):
    assert input_val.upper() == expected
```

Use `pytest.param(..., id="...")` for readable test IDs. Don't parameterize unrelated behaviors — if the test logic differs, write separate tests.

## Fixtures

### Function-scoped fixtures (default, preferred)

```python
@pytest.fixture()
def db_connection():
    conn = create_connection(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    yield conn
    conn.close()

def test_insert_user(db_connection):
    db_connection.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    rows = db_connection.execute("SELECT name FROM users").fetchall()
    assert rows == [("Alice",)]
```

### Fixture scopes

```python
@pytest.fixture(scope="session")
def app_config():
    """Created once per entire test session — use for expensive, immutable setup."""
    return load_config("test")

@pytest.fixture(scope="module")
def http_client(app_config):
    """Created once per test module."""
    client = HTTPClient(app_config["base_url"])
    yield client
    client.close()

@pytest.fixture()  # scope="function" is the default
def fresh_user(db_connection):
    """Created fresh for every test — use for mutable state."""
    return create_user(db_connection, name="TestUser")
```

### Autouse fixtures for state reset

Use `autouse=True` to reset global/module-level state between tests:

```python
@pytest.fixture(autouse=True)
def _reset_global_state():
    """Ensure clean state for every test."""
    original = app.config.copy()
    yield
    app.config = original
```

### Fixture files

Store XML, JSON, and binary test data in `tests/fixtures/`. Load via `Path`:

```python
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

@pytest.fixture()
def sample_response() -> dict:
    import json
    return json.loads((FIXTURES / "api_response.json").read_text())

@pytest.fixture()
def image_bytes() -> bytes:
    return (FIXTURES / "sample.jpg").read_bytes()
```

### Shared fixtures in `conftest.py`

Only put fixtures in `conftest.py` when they're needed across multiple test files. Keep test-file-specific fixtures in the test file itself.

### Built-in fixtures

```python
def test_file_writing(tmp_path):
    """tmp_path provides a fresh temporary directory per test."""
    file = tmp_path / "output.txt"
    file.write_text("content")
    assert file.read_text() == "content"

def test_env_override(monkeypatch):
    """monkeypatch sets/deletes env vars, attributes, dict items — auto-reverted."""
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setattr(mymodule, "DEBUG", True)
    assert os.environ["API_KEY"] == "test-key"

def test_captures_output(capsys):
    """capsys captures stdout/stderr."""
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"

def test_logging(caplog):
    """caplog captures log records."""
    import logging
    with caplog.at_level(logging.WARNING):
        logging.warning("something happened")
    assert "something happened" in caplog.text
```

## Mocking

### Mock at the boundary, not what you own

Test your code with real implementations when possible. Mock **external** services and I/O, not internal classes.

```python
from unittest.mock import patch, Mock, AsyncMock

# Good: mock the external HTTP call
def test_get_user_calls_api():
    mock_response = Mock()
    mock_response.json.return_value = {"id": 1, "name": "Alice"}
    mock_response.raise_for_status.return_value = None

    with patch("myapp.client.requests.get", return_value=mock_response) as mock_get:
        user = get_user(1)

        assert user["name"] == "Alice"
        mock_get.assert_called_once_with("https://api.example.com/users/1")

# Bad: mocking your own internal class
def test_service():
    with patch("myapp.service.UserRepository"):  # Don't mock what you own
        ...
```

### Async mocking

```python
from unittest.mock import AsyncMock, patch

async def test_async_fetch():
    with patch("myapp.client.fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"data": "test"}
        result = await process_data()
        assert result == {"data": "test"}
```

### HTTP mocking with respx (for httpx)

```python
import httpx
import respx

@respx.mock(assert_all_called=False)
async def test_fetch_returns_data(respx_mock):
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"key": "value"})
    )

    result = await fetch_data("https://api.example.com/data")

    assert result == {"key": "value"}
```

### HTTP mocking with responses (for requests)

```python
import responses

@responses.activate
def test_api_call():
    responses.add(
        responses.GET,
        "https://api.example.com/data",
        json={"key": "value"},
        status=200,
    )
    result = fetch_data()
    assert result == {"key": "value"}
```

### Testing side effects and call sequences

```python
from unittest.mock import Mock, call

def test_retries_on_transient_error():
    client = Mock()
    client.request.side_effect = [
        ConnectionError("Failed"),
        ConnectionError("Failed"),
        {"status": "ok"},
    ]
    service = ServiceWithRetry(client, max_retries=3)
    result = service.fetch()

    assert result == {"status": "ok"}
    assert client.request.call_count == 3

def test_gives_up_after_max_retries():
    client = Mock()
    client.request.side_effect = ConnectionError("Failed")
    service = ServiceWithRetry(client, max_retries=3)

    with pytest.raises(ConnectionError):
        service.fetch()
    assert client.request.call_count == 3
```

### Mocking time with freezegun

```python
from freezegun import freeze_time
from datetime import datetime

@freeze_time("2026-01-15 10:00:00")
def test_token_expiry():
    token = create_token(expires_in_seconds=3600)
    assert token.expires_at == datetime(2026, 1, 15, 11, 0, 0)

def test_time_progression():
    with freeze_time("2026-01-01") as frozen_time:
        item = create_item()
        assert item.created_at == datetime(2026, 1, 1)
        frozen_time.move_to("2026-01-15")
        assert item.age_days == 14
```

## Error Testing

```python
import pytest

def test_raises_on_invalid_input():
    with pytest.raises(ValueError, match="must be positive"):
        calculate(-1)

def test_exception_info():
    with pytest.raises(ValueError) as exc_info:
        int("not a number")
    assert "invalid literal" in str(exc_info.value)

async def test_async_raises():
    with pytest.raises(ConnectionError):
        await connect_to_invalid_host()
```

### Always test error paths

```python
def test_get_user_raises_not_found():
    with pytest.raises(UserNotFoundError) as exc_info:
        service.get_user("nonexistent-id")
    assert "nonexistent-id" in str(exc_info.value)

def test_create_user_rejects_invalid_email():
    with pytest.raises(ValueError, match="Invalid email"):
        service.create_user({"email": "not-an-email"})
```

## Async Testing

### With pytest-asyncio

```python
# pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"  # Recommended: no decorators needed

# With asyncio_mode = "auto" — just write async functions:
async def test_async_operation():
    result = await some_async_function()
    assert result == expected

# Without auto mode — need the marker:
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result == expected
```

### Async fixtures

```python
@pytest.fixture()
async def async_client():
    client = AsyncClient()
    await client.connect()
    yield client
    await client.disconnect()

async def test_with_async_client(async_client):
    result = await async_client.fetch("/data")
    assert result is not None
```

## Performance Testing

Use `time.perf_counter()` for benchmarks and `asyncio.TaskGroup` for concurrency:

```python
import asyncio
import time

async def test_concurrent_requests_are_parallel():
    """N concurrent requests should complete in ~1x time, not Nx."""
    delay = 0.05
    n = 8

    async def slow_fetch(i):
        await asyncio.sleep(delay)
        return i

    start = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(slow_fetch(i)) for i in range(n)]
    elapsed = time.perf_counter() - start

    assert elapsed < delay * n * 0.5  # Should be ~1x, not 8x
```

## Test Markers

```python
@pytest.mark.slow
def test_slow_operation(): ...

@pytest.mark.integration
def test_database_integration(): ...

@pytest.mark.skip(reason="Feature not implemented yet")
def test_future_feature(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_specific(): ...

@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug(): ...
```

```bash
pytest -m slow            # Run only slow tests
pytest -m "not slow"      # Skip slow tests
pytest -m integration     # Run integration tests
```

## Test Organization

```
tests/
    conftest.py             # Shared fixtures only
    fixtures/               # XML, JSON, binary test data
        api_response.json
        sample.jpg
    test_models.py          # One test file per source module
    test_client.py
    test_operations.py
```

**One test file per source module** — `test_client.py` tests `client.py`. Each test file should be self-contained with its own helpers and mock data. Fixtures in `conftest.py` only for truly shared setup.

## Running Tests

```bash
pytest                             # Run all tests
pytest tests/test_client.py        # Run specific file
pytest -k "test_login"             # Run tests matching pattern
pytest -m "not integration"        # Exclude by marker
pytest -x                          # Stop on first failure
pytest -v                          # Verbose output
pytest --tb=short                  # Shorter tracebacks
pytest --cov=myapp                 # With coverage
pytest --cov=myapp --cov-report=term-missing  # Show uncovered lines
pytest --cov=myapp --cov-fail-under=80        # Fail below threshold
```

## Inline Snapshots

Use `inline-snapshot` for testing complex structures without hand-writing expected values:

```python
from inline_snapshot import snapshot

def test_schema_generation():
    schema = generate_schema(MyModel)
    assert schema == snapshot()  # Auto-populated on first run
```

```bash
pytest --inline-snapshot=create   # Populate empty snapshots
pytest --inline-snapshot=fix      # Update after intentional changes
```

## What to Test vs Skip

- **Test**: behavior, return values, error handling, edge cases, boundary conditions
- **Skip**: log messages, `__init__.py` re-exports, config constants, telemetry attributes

## Checklist

Before submitting tests:
- [ ] Each test tests one behavior
- [ ] Descriptive `test_<subject>_<scenario>` names
- [ ] Imports at module level
- [ ] Parameterization with `pytest.param(id=...)` for variations
- [ ] Mocks at external boundaries, not internal classes
- [ ] Error paths tested, not just happy paths
- [ ] No shared mutable state between tests (autouse fixtures if needed)
- [ ] Fixture files in `tests/fixtures/` for complex test data
- [ ] Tests are deterministic — no flaky timing or network dependencies
