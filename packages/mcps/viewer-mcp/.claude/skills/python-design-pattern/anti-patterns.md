# Anti-Patterns Checklist

Use this as a checklist when reviewing code, before finalizing implementations, or when debugging issues that might stem from known bad practices.

## Exposed Internal Types

```python
# BAD: Leaking ORM model to API
@app.get("/users/{id}")
def get_user(id: str) -> UserModel:  # SQLAlchemy model
    return db.query(UserModel).get(id)

# GOOD: Use response schemas
@app.get("/users/{id}")
def get_user(id: str) -> UserResponse:
    user = db.query(UserModel).get(id)
    return UserResponse.from_orm(user)
```

## Scattered Timeout/Retry Logic

```python
# BAD: Timeout logic duplicated everywhere
def fetch_user(user_id):
    try:
        return requests.get(url, timeout=30)
    except Timeout:
        logger.warning("Timeout fetching user")
        return None

def fetch_orders(user_id):
    try:
        return requests.get(url, timeout=30)
    except Timeout:
        logger.warning("Timeout fetching orders")
        return None

# GOOD: Centralized retry logic
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def http_get(url: str) -> Response:
    return requests.get(url, timeout=30)
```

## Double Retry

```python
# BAD: Retrying at multiple layers
@retry(max_attempts=3)  # Application retry
def call_service():
    return client.request()  # Client also has retry configured!
```

Retry at one layer only. Know your infrastructure's retry behavior.

## Hard-Coded Configuration

```python
# BAD: Secrets and config in code
DB_HOST = "prod-db.example.com"
API_KEY = "sk-12345"

# GOOD: Environment variables with typed settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = Field(alias="DB_HOST")
    api_key: str = Field(alias="API_KEY")

settings = Settings()
```

## Bare Exception Handling

```python
# BAD: Swallowing all exceptions
try:
    process()
except Exception:
    pass  # Silent failure — bugs hidden forever

# GOOD: Catch specific exceptions
try:
    process()
except ConnectionError as e:
    logger.warning("Connection failed, will retry", error=str(e))
    raise
except ValueError as e:
    logger.error("Invalid input", error=str(e))
    raise BadRequestError(str(e))
```

## Ignored Partial Failures

```python
# BAD: Stops on first error, entire batch lost
def process_batch(items):
    results = []
    for item in items:
        result = process(item)  # Raises on error — batch aborted
        results.append(result)
    return results

# GOOD: Capture both successes and failures
def process_batch(items) -> BatchResult:
    succeeded = {}
    failed = {}
    for idx, item in enumerate(items):
        try:
            succeeded[idx] = process(item)
        except Exception as e:
            failed[idx] = e
    return BatchResult(succeeded, failed)
```

## Missing Input Validation

```python
# BAD: No validation — crashes deep in code on bad input
def create_user(data: dict):
    return User(**data)

# GOOD: Validate early at API boundaries
def create_user(data: dict) -> User:
    validated = CreateUserInput.model_validate(data)
    return User.from_input(validated)
```

## Unclosed Resources

```python
# BAD: File never closed if read() raises
def read_file(path):
    f = open(path)
    return f.read()

# GOOD: Context managers
def read_file(path):
    with open(path) as f:
        return f.read()
```

## Blocking in Async

```python
# BAD: Blocks the entire event loop
async def fetch_data():
    time.sleep(1)          # Blocks everything!
    response = requests.get(url)  # Also blocks!

# GOOD: Async-native libraries
async def fetch_data():
    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
```

## Missing Type Hints

```python
# BAD: No types — callers guess at contracts
def process(data):
    return data["value"] * 2

def get_users() -> list:  # Untyped collection
    ...

# GOOD: Annotate all public functions
def process(data: dict[str, int]) -> int:
    return data["value"] * 2

def get_users() -> list[User]:
    ...
```

## Only Testing Happy Paths

```python
# BAD: Only tests success case
def test_create_user():
    user = service.create_user(valid_data)
    assert user.id is not None

# GOOD: Test error conditions and edge cases too
def test_create_user_success():
    user = service.create_user(valid_data)
    assert user.id is not None

def test_create_user_invalid_email():
    with pytest.raises(ValueError, match="Invalid email"):
        service.create_user(invalid_email_data)

def test_create_user_duplicate_email():
    service.create_user(valid_data)
    with pytest.raises(ConflictError):
        service.create_user(valid_data)
```

## Over-Mocking

```python
# BAD: Mocking everything — test doesn't verify real behavior
def test_user_service():
    mock_repo = Mock()
    mock_cache = Mock()
    mock_logger = Mock()
    mock_metrics = Mock()
    ...
```

Use integration tests for critical paths. Mock only external services.

## Quick Reference

| Anti-Pattern | Fix |
|---|---|
| Exposed internal types | DTO/response schemas |
| Scattered retry logic | Centralized decorators/client wrappers |
| Double retry | Retry at one layer only |
| Hard-coded config | Environment variables + pydantic-settings |
| Mixed I/O + logic | Repository pattern (see Pattern 2-3) |
| Bare except | Catch specific exceptions |
| Batch stops on error | Return BatchResult with successes/failures |
| No validation | Validate at boundaries with Pydantic |
| Unclosed resources | Context managers |
| Blocking in async | Async-native libraries |
| Missing types | Type annotations on all public APIs |
| Only happy path tests | Test errors and edge cases |
| Over-mocking | Mock external boundaries only |

## Review Checklist

Before finalizing code, verify:

- [ ] No scattered timeout/retry logic (centralized)
- [ ] No double retry (app + infrastructure)
- [ ] No hard-coded configuration or secrets
- [ ] No exposed internal types (ORM models, protobufs)
- [ ] No mixed I/O and business logic (see Pattern 2-3)
- [ ] No bare `except Exception: pass`
- [ ] No ignored partial failures in batches
- [ ] No missing input validation at boundaries
- [ ] No unclosed resources (using context managers)
- [ ] No blocking calls in async code
- [ ] All public functions have type hints
- [ ] Collections have type parameters
- [ ] Error paths are tested
- [ ] Edge cases are covered
