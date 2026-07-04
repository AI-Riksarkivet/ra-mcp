---
name: python-type-safety
description: Modern Python type safety with type hints, generics, protocols, and strict type checking using ty and ruff. Use when adding type annotations, implementing generic classes, defining structural interfaces, configuring ty/ruff, or writing type-safe Python 3.13+/3.14+ code. Triggers on mentions of type hints, typing, TypeVar, Protocol, overload, TypeIs, Pydantic models, ty check, ruff type rules, or any static type analysis in Python.
---

# Python Type Safety (3.13+ / 3.14+)

Modern Python type safety using the Astral toolchain: **ty** for type checking and language server, **ruff** for linting (including annotation enforcement), and **uv** for package management. All examples target Python 3.13+ with 3.14 deferred annotations as the default.

## Toolchain

| Tool | Role | Install |
|------|------|---------|
| **ty** | Type checker + LSP (10-100x faster than mypy) | `uv tool install ty@latest` |
| **ruff** | Linter + formatter (replaces flake8, black, isort) | `uv tool install ruff` |
| **uv** | Package manager + env management | [astral.sh/uv](https://docs.astral.sh/uv/) |

ty is the type checker from Astral (the creators of ruff and uv). It is written in Rust, provides a full language server (LSP) with code navigation, completions, and inlay hints, and supports advanced features like intersection types, reachability analysis, and gradual typing guarantees.

## Key Python Version Features

### Python 3.12
- **PEP 695** — Type parameter syntax: `def first[T](items: list[T]) -> T:`
- **PEP 695** — `type` statement for aliases: `type Point = tuple[float, float]`

### Python 3.13
- **PEP 696** — TypeVar/ParamSpec/TypeVarTuple defaults: `class Box[T = int]:`
- **PEP 742** — `TypeIs` for proper bidirectional type narrowing
- **PEP 705** — `ReadOnly` for TypedDict items
- **PEP 702** — `warnings.deprecated()` decorator with type system support

### Python 3.14
- **PEP 649/749** — Deferred evaluation of annotations (no more `from __future__ import annotations`, no more forward reference strings)
- **PEP 758** — `except` and `except*` expressions may omit brackets

## Fundamental Patterns

### Pattern 1: Annotate All Public Signatures

Every public function, method, and class should have type annotations. Use native generics everywhere (no `typing.List`, `typing.Dict`, etc. — those are ancient history).

```python
from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str | None = None


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def find_by_id(self, user_id: str) -> User | None:
        ...

    async def find_by_email(self, email: str) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...
```

### Pattern 2: Type Narrowing with TypeIs (3.13+)

`TypeIs` provides proper bidirectional narrowing — when the guard returns `False`, the type checker narrows the else branch too (unlike the older `TypeGuard`).

```python
from typing import TypeIs


def is_string(x: int | str) -> TypeIs[str]:
    return isinstance(x, str)


def process(value: int | str) -> str:
    if is_string(value):
        return value.upper()       # value: str
    else:
        return str(value * 2)      # value: int (properly narrowed)


def is_valid_user(obj: dict | User) -> TypeIs[User]:
    return isinstance(obj, User)
```

Use `TypeIs` over `TypeGuard` in all new code. `TypeGuard` only narrows the true branch; `TypeIs` narrows both.

### Pattern 3: Modern Generic Classes (3.12+ Syntax)

Use the built-in type parameter syntax — no `TypeVar` boilerplate needed.

```python
from pydantic import BaseModel


class Result[T, E: Exception]:
    """Either a success value or an error."""

    def __init__(
        self,
        value: T | None = None,
        error: E | None = None,
    ) -> None:
        if (value is None) == (error is None):
            raise ValueError("Exactly one of value or error must be set")
        self._value = value
        self._error = error

    @property
    def is_success(self) -> bool:
        return self._error is None

    def unwrap(self) -> T:
        if self._error is not None:
            raise self._error
        return self._value  # type: ignore[return-value]

    def unwrap_or(self, default: T) -> T:
        if self._error is not None:
            return default
        return self._value  # type: ignore[return-value]


class ConfigError(Exception): ...

class Config(BaseModel):
    host: str
    port: int


def parse_config(path: str) -> Result[Config, ConfigError]:
    try:
        return Result(value=Config.model_validate_json(open(path).read()))
    except Exception as e:
        return Result(error=ConfigError(str(e)))
```

### Pattern 4: TypeVar Defaults (3.13+)

Generic parameters can now have defaults, reducing boilerplate for common cases.

```python
class Response[T = dict]:
    def __init__(self, data: T, status: int = 200) -> None:
        self.data = data
        self.status = status


# Uses default: Response[dict]
r1 = Response({"ok": True})

# Explicit: Response[list[str]]
r2 = Response(["a", "b"], status=201)


class Container[T = int]:
    def __init__(self, value: T) -> None:
        self.value = value

# Container[int] by default
c = Container(42)
```

### Pattern 5: Protocols for Structural Typing

Define interfaces without inheritance — duck typing with full type safety.

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, data: dict) -> "Serializable": ...


class Closeable(Protocol):
    def close(self) -> None: ...


class AsyncCloseable(Protocol):
    async def close(self) -> None: ...


class HasId(Protocol):
    @property
    def id(self) -> str: ...


# Any class with matching methods satisfies the protocol — no inheritance needed
class User:
    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(id=data["id"], name=data["name"])


def serialize(obj: Serializable) -> str:
    import json
    return json.dumps(obj.to_dict())


serialize(User("1", "Alice"))  # Works — User matches Protocol
isinstance(User("1", "Alice"), Serializable)  # True at runtime
```

### Pattern 6: Deferred Annotations (3.14+)

In Python 3.14, annotations are evaluated lazily. Forward references just work — no string quoting, no `from __future__ import annotations`.

```python
# This just works in 3.14+ — no special imports needed
class TreeNode[T]:
    value: T
    children: list[TreeNode[T]]  # Forward reference, no quotes needed

    def __init__(self, value: T) -> None:
        self.value = value
        self.children = []

    def add_child(self, value: T) -> TreeNode[T]:
        child = TreeNode(value)
        self.children.append(child)
        return child


# Mutually recursive types — also just work
class Order:
    customer: Customer  # Forward reference resolved lazily
    total: float

class Customer:
    orders: list[Order]
    name: str
```

The new `annotationlib` module provides tools for introspecting deferred annotations when needed at runtime (VALUE, FORWARDREF, STRING formats).

## Advanced Patterns

### Pattern 7: Discriminated Unions

Use `Literal` types for tagged unions with exhaustive pattern matching.

```python
from typing import Literal
from pydantic import BaseModel


class EmailNotification(BaseModel):
    type: Literal["email"] = "email"
    to: str
    subject: str
    body: str


class SMSNotification(BaseModel):
    type: Literal["sms"] = "sms"
    to: str
    message: str


class PushNotification(BaseModel):
    type: Literal["push"] = "push"
    device_token: str
    title: str
    body: str


type Notification = EmailNotification | SMSNotification | PushNotification


async def send_notification(notification: Notification) -> bool:
    match notification.type:
        case "email":
            return await send_email(notification.to, notification.subject, notification.body)
        case "sms":
            return await send_sms(notification.to, notification.message)
        case "push":
            return await send_push(notification.device_token, notification.title, notification.body)
```

### Pattern 8: ParamSpec for Type-Safe Decorators

Preserve function signatures through decorators.

```python
from typing import ParamSpec, Callable, Awaitable
from functools import wraps
import time

type P = ParamSpec  # Can't use type statement for ParamSpec yet

# Use the traditional form for ParamSpec
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timing(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


def retry(
    max_attempts: int = 3,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception: Exception | None = None
            for _ in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
            raise last_exception or RuntimeError("Retry failed")
        return wrapper
    return decorator


@retry(max_attempts=3, exceptions=(ValueError, IOError))
@timing
def fetch_data(url: str, timeout: int = 30) -> dict:
    ...
```

Note: Python 3.12 introduced `def f[**P, R](...)` syntax for ParamSpec in function signatures, but `ParamSpec` and `TypeVar` are still needed for module-level decorator definitions.

### Pattern 9: Conditional Types with Overloads

Return different types based on argument values.

```python
from typing import overload, Literal


@overload
def fetch(url: str, *, as_json: Literal[True]) -> dict: ...
@overload
def fetch(url: str, *, as_json: Literal[False] = False) -> str: ...

def fetch(url: str, *, as_json: bool = False) -> dict | str:
    import requests
    response = requests.get(url)
    if as_json:
        return response.json()
    return response.text


# Type checker knows the exact return type
data: dict = fetch("https://api.example.com", as_json=True)
text: str = fetch("https://api.example.com")
```

### Pattern 10: Generic Repository with Pydantic

Type-safe data access using Pydantic models.

```python
from typing import Protocol
from pydantic import BaseModel
from abc import abstractmethod


class Repository[T: BaseModel, ID](Protocol):
    async def get(self, id: ID) -> T | None: ...
    async def get_all(self) -> list[T]: ...
    async def save(self, entity: T) -> T: ...
    async def delete(self, id: ID) -> bool: ...


class User(BaseModel):
    id: str
    name: str
    email: str


class SQLRepository[T: BaseModel]:
    def __init__(self, session: AsyncSession, model_cls: type[T]) -> None:
        self._session = session
        self._model_cls = model_cls

    async def get(self, id: str) -> T | None:
        ...

    async def save(self, entity: T) -> T:
        data = entity.model_dump()
        ...
        return entity


class UserRepository(SQLRepository[User]):
    async def find_by_email(self, email: str) -> User | None:
        ...
```

### Pattern 11: Builder Pattern with Self

`Self` (3.11+) enables proper return typing for method chaining in inheritance hierarchies.

```python
from typing import Self
from pydantic import BaseModel


class QueryBuilder[T]:
    def __init__(self, model: type[T]) -> None:
        self._model = model
        self._filters: list[str] = []
        self._order_by: str | None = None
        self._limit: int | None = None

    def filter(self, condition: str) -> Self:
        self._filters.append(condition)
        return self

    def order_by(self, field: str) -> Self:
        self._order_by = field
        return self

    def limit(self, n: int) -> Self:
        self._limit = n
        return self

    def build(self) -> str:
        query = f"SELECT * FROM {self._model.__name__}"
        if self._filters:
            query += " WHERE " + " AND ".join(self._filters)
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query
```

### Pattern 12: ReadOnly TypedDict (3.13+)

Mark specific TypedDict fields as immutable for type checkers.

```python
from typing import TypedDict, ReadOnly, Required, NotRequired


class Config(TypedDict):
    host: ReadOnly[str]          # Cannot be modified after creation
    port: ReadOnly[int]
    debug: NotRequired[bool]     # Optional, but mutable if present


class APIResponse(TypedDict):
    status: ReadOnly[Required[int]]
    data: dict                   # Mutable
    error: NotRequired[str]


def update_config(config: Config) -> None:
    config["debug"] = True        # OK — mutable field
    config["host"] = "new.host"   # Type error — ReadOnly
```

### Pattern 13: Typed Event System

Type-safe event bus using generics.

```python
import asyncio
from typing import Callable, Awaitable
from pydantic import BaseModel


class Event(BaseModel):
    timestamp: float


class UserCreatedEvent(Event):
    user_id: int
    email: str


class OrderPlacedEvent(Event):
    order_id: int
    user_id: int
    total: float


class TypedEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = {}

    def subscribe[E: Event](
        self,
        event_type: type[E],
        handler: Callable[[E], Awaitable[None]],
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish[E: Event](self, event: E) -> None:
        handlers = self._handlers.get(type(event), [])
        await asyncio.gather(*[h(event) for h in handlers])
```

### Pattern 14: Annotated for Rich Metadata

Combine type information with validation constraints (works great with Pydantic).

```python
from typing import Annotated
from pydantic import BaseModel, Field


type UserId = Annotated[int, Field(gt=0)]
type Email = Annotated[str, Field(pattern=r"^[\w.-]+@[\w.-]+\.\w+$")]
type Age = Annotated[int, Field(ge=0, le=150)]
type NonEmpty = Annotated[str, Field(min_length=1)]


class CreateUserRequest(BaseModel):
    name: NonEmpty
    email: Email
    age: Age


class UserResponse(BaseModel):
    id: UserId
    name: str
    email: str
```

### Pattern 15: Callable Types with Protocol

When you need named parameters on callable types, use Protocol.

```python
from typing import Protocol
from collections.abc import Callable, Awaitable


# Simple callables — use Callable
type ProgressCallback = Callable[[int, int], None]
type AsyncHandler = Callable[..., Awaitable[dict]]

# Named parameters — use Protocol
class OnProgress(Protocol):
    def __call__(
        self,
        current: int,
        total: int,
        *,
        message: str = "",
    ) -> None: ...


def process_items(
    items: list[str],
    on_progress: OnProgress | None = None,
) -> list[str]:
    results = []
    for i, item in enumerate(items):
        if on_progress:
            on_progress(i, len(items), message=f"Processing {item}")
        results.append(item.upper())
    return results
```

### Pattern 16: Recursive Types

```python
from typing import TypeAlias
from collections.abc import Iterator


# JSON type (recursive)
type JsonPrimitive = str | int | float | bool | None
type JsonArray = list[JsonValue]
type JsonObject = dict[str, JsonValue]
type JsonValue = JsonPrimitive | JsonArray | JsonObject


def parse_json(text: str) -> JsonValue:
    import json
    return json.loads(text)


# Tree structure
class TreeNode[T]:
    value: T
    children: list[TreeNode[T]]

    def __init__(self, value: T) -> None:
        self.value = value
        self.children = []

    def traverse(self) -> Iterator[T]:
        yield self.value
        for child in self.children:
            yield from child.traverse()
```

### Pattern 17: Deprecation Markers (3.13+)

Mark deprecated APIs so type checkers emit warnings.

```python
import warnings


@warnings.deprecated("Use process_v2() instead")
def process(data: str) -> str:
    return process_v2(data)


def process_v2(data: str) -> str:
    return data.upper()


# Type checker will warn when calling process()
result = process("hello")  # Deprecated: Use process_v2() instead
```

## Configuration

### ty Configuration

```toml
# pyproject.toml
[tool.ty.environment]
python-version = "3.14"

[tool.ty.rules]
# Promote common issues to errors
unresolved-import = "error"
invalid-assignment = "error"
invalid-argument-type = "error"
invalid-return-type = "error"

# Useful warnings
unused-ignore-comment = "warn"
possibly-missing-import = "warn"
deprecated = "warn"
division-by-zero = "warn"

[tool.ty.analysis]
# Suppress known unresolvable third-party imports
allowed-unresolved-imports = ["_typeshed.**"]

# Per-path overrides for legacy code
[[tool.ty.overrides]]
include = ["src/legacy/**"]
rules = { unresolved-attribute = "ignore" }
```

### ruff Configuration (Annotation Enforcement)

Use ruff's `ANN` rules (flake8-annotations) to enforce annotation coverage, and `UP` rules (pyupgrade) to modernize syntax.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py313"
line-length = 120

[tool.ruff.lint]
select = [
    "E",    # pycodestyle
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade — modernize syntax (e.g. remove old typing imports)
    "ANN",  # flake8-annotations — enforce type annotations
    "B",    # bugbear
    "SIM",  # simplify
    "TCH",  # flake8-type-checking — move type-only imports behind TYPE_CHECKING
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN"]  # Don't require annotations in tests

[tool.ruff.lint.flake8-type-checking]
runtime-evaluated-base-classes = ["pydantic.BaseModel"]
```

### Running in CI

```bash
# Type check
ty check src/

# Type check in watch mode (development)
ty check --watch

# Lint + format
ruff check src/
ruff format src/

# All three in CI
uv run ty check src/ && uv run ruff check src/
```

### Inline Suppression

```python
# Suppress a specific ty diagnostic
result = greet(42)  # ty: ignore[invalid-argument-type]

# Suppress ruff
x = 1  # noqa: ANN001
```

## Best Practices

1. **Use Pydantic for data models** — Never plain dataclasses. Pydantic gives you runtime validation, serialization, and schema generation alongside type safety.
2. **Annotate all public APIs** — Functions, methods, class attributes. Let ruff's `ANN` rules enforce this.
3. **Use `T | None`** — Modern union syntax everywhere. Never `Optional[T]` or `Union[X, Y]`.
4. **Use native generics** — `list[str]`, `dict[str, int]`, `tuple[int, ...]`. Never import from `typing`.
5. **Use 3.12+ type parameter syntax** — `def f[T](x: T) -> T:` and `class C[T]:` instead of `TypeVar`.
6. **Use `TypeIs` over `TypeGuard`** — Proper bidirectional narrowing (3.13+).
7. **Use `type` statement for aliases** — `type Point = tuple[float, float]` instead of `TypeAlias`.
8. **Prefer Protocols over ABCs** — Structural typing is more flexible than nominal typing.
9. **Use abstract collection types for parameters** — `Iterable[str]`, `Sequence[str]`, `Mapping[str, int]` from `collections.abc`.
10. **Minimize `Any`** — Use specific types or generics. `Any` is acceptable for truly dynamic data or untyped third-party code.
11. **Use `Annotated` with Pydantic `Field`** — Rich type aliases that carry validation constraints.
12. **Run ty + ruff in CI** — ty for type checking, ruff for annotation enforcement and modernization.